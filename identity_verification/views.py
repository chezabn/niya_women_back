import os

from django.core.mail import send_mail
from django.db import connections
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from niya import settings
from publication.pagination import FeedPagination
from .constants import (
    EMAIL_SUBJECT_VERIFICATION_REJECTED,
    EMAIL_BODY_VERIFICATION_REJECTED,
    EMAIL_SUBJECT_VERIFICATION_APPROVED,
    EMAIL_BODY_VERIFICATION_APPROVED,
    EMAIL_SUBJECT_NEW_VERIFICATION_REQUEST,
    EMAIL_BODY_NEW_VERIFICATION_REQUEST,
)
from .models import IdentityVerificationRequest
from .serializers import (
    VerificationRequestSerializer,
    AdminVerificationReviewSerializer, IdentityVerificationDetailSerializer,
)


class Healthcheck(APIView):
    """
    Healthcheck endpoint for the Authentication API.

    Performs a simple check to ensure the application and database connection are operational.

    :param request: HTTP GET request
    :type request: rest_framework.request.Request
    :return: JSON response with API name, version, and database connection status
    :rtype: rest_framework.response.Response
    """

    def get(self, request):
        db_conn = connections["default"]
        try:
            cursor = db_conn.cursor()
        except Exception as e:
            return Response(
                {
                    "name": "Niyya Identity Verification",
                    "version": "1.0.0",
                    "environment": os.getenv("ENVIRONMENT", "dev"),
                    "status": "Database connection failed",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "name": "Niyya Identity Verification",
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "dev"),
                "status": "Database connection established",
            },
            status=status.HTTP_200_OK,
        )


class SubmitIdentityVerificationView(APIView):
    """
    Permet à une utilisatrice de soumettre ses documents pour vérification.
    Accessible même si le compte n'est pas encore actif (is_active=False).
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        # Vérifier si une demande existe déjà
        if hasattr(user, "identity_request"):
            req = user.identity_request
            if req.status == "PENDING":
                return Response(
                    {"detail": "Une demande est déjà en cours de traitement."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif req.status == "APPROVED":
                return Response(
                    {"detail": "Votre identité est déjà vérifiée."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Si REJECTED, on permet de refaire une demande (on met à jour l'existant ou on en crée un nouveau)
            # Ici, on choisit de mettre à jour l'existant pour garder l'historique simple
            req.status = "PENDING"
            req.rejection_reason = ""
            req.reviewed_by = None
            req.reviewed_at = None
            req.save()
            instance = req
        else:
            instance = None

        serializer = VerificationRequestSerializer(
            instance, data=request.data, partial=True
        )
        if serializer.is_valid():
            obj = serializer.save(user=user)
            try:
                admin_link = request.build_absolute_uri(
                    f"/api/identification/admin/identity/{obj.id}/review/"
                )
                message_body = EMAIL_BODY_NEW_VERIFICATION_REQUEST.format(
                    username=user.username,
                    email=user.email,
                    created_at=obj.created_at.strftime("%d/%m/%Y à %H:%M"),
                    admin_link=admin_link,
                )

                from django.contrib.auth import get_user_model

                admin_email_list = list(
                    get_user_model()
                    .objects.filter(is_staff=True)
                    .values_list("email", flat=True)
                )
                send_mail(
                    subject=EMAIL_SUBJECT_NEW_VERIFICATION_REQUEST,
                    message=message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_email_list,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Erreur envoi email validation: {e}")
            return Response(
                {
                    "message": "Documents soumis avec succès. En attente de validation par l'admin.",
                    "id": obj.id,
                },
                status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminReviewIdentityView(APIView):
    """
    Permet à un administrateur de valider ou rejeter une demande.
    """

    permission_classes = [permissions.IsAdminUser]

    @staticmethod
    def delete_verification_images(verification_req):
        image_fields = ("id_card_front", "selfie_with_id")
        for field_name in image_fields:
            image = getattr(verification_req, field_name)
            if image and image.name:
                image.storage.delete(image.name)
                setattr(verification_req, field_name, "")

        verification_req.save(update_fields=image_fields)

    def post(self, request, pk):
        verification_req = get_object_or_404(IdentityVerificationRequest, pk=pk)
        serializer = AdminVerificationReviewSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            action = data["action"]
            user = verification_req.user  # On récupère l'utilisatrice concernée
            if action == "approve":
                # 1. Valider la demande (change le statut et active le compte)
                verification_req.approve(request.user)
                self.delete_verification_images(verification_req)
                # 2. Envoyer l'email de félicitations
                try:
                    send_mail(
                        subject=EMAIL_SUBJECT_VERIFICATION_APPROVED,
                        message=EMAIL_BODY_VERIFICATION_APPROVED.format(
                            first_name=user.first_name or user.username
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    # On logge l'erreur mais on ne bloque pas la validation
                    # La validation est déjà faite en BDD
                    print(f"Erreur envoi email validation: {e}")

                return Response(
                    {
                        "message": "Identité validée. Le compte a été activé et un email a été envoyé."
                    },
                    status=status.HTTP_200_OK,
                )

            elif action == "reject":
                reason = data.get("rejection_reason", "Non spécifié")
                # 1. Rejeter la demande
                verification_req.reject(request.user, reason)
                self.delete_verification_images(verification_req)
                # 2. Envoyer l'email de rejet
                try:
                    send_mail(
                        subject=EMAIL_SUBJECT_VERIFICATION_REJECTED,
                        message=EMAIL_BODY_VERIFICATION_REJECTED.format(
                            first_name=user.first_name or user.username,
                            rejection_reason=reason,
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Erreur envoi email rejet: {e}")

                return Response(
                    {
                        "message": "Demande rejetée. Un email explicatif a été envoyé à l'utilisatrice."
                    },
                    status=status.HTTP_200_OK,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminIdentityVerificationListView(APIView):
    """
    Permet à un membre de l'équipe de validation de consulter
    toutes les demandes de vérification d'identité.
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        verification_requests = (
            IdentityVerificationRequest.objects
            .select_related("user", "reviewed_by")
            .order_by("-created_at")
        )

        status_filter = request.query_params.get("status", "").strip().lower()
        status_aliases = {
            "pending": "PENDING",
            "approved": "APPROVED",
            "approve": "APPROVED",
            "rejected": "REJECTED",
            "reject": "REJECTED",
        }
        if status_filter:
            if status_filter not in status_aliases:
                return Response(
                    {"status": "Valeur invalide. Utilisez pending, approved ou rejected."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            verification_requests = verification_requests.filter(
                status=status_aliases[status_filter]
            )

        paginator = FeedPagination()
        page = paginator.paginate_queryset(verification_requests, request, view=self)
        serializer = IdentityVerificationDetailSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(serializer.data)

class ReviewIdentityView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        verification_request = get_object_or_404(
            IdentityVerificationRequest,
            pk=pk,
        )

        serializer = IdentityVerificationDetailSerializer(
            verification_request
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class IdentityVerificationStatusView(APIView):
    """
    Permet à l'utilisatrice de consulter le statut de sa demande
    de vérification d'identité.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            verification_request = request.user.identity_request
        except IdentityVerificationRequest.DoesNotExist:
            return Response(
                {
                    "has_request": False,
                    "status": None,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "has_request": True,
                "status": verification_request.status,
                "rejection_reason": verification_request.rejection_reason,
                "created_at": verification_request.created_at,
                "updated_at": verification_request.updated_at,
            },
            status=status.HTTP_200_OK,
        )
