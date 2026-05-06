import os

from django.db import connections
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import IdentityVerificationRequest
from .serializers import VerificationRequestSerializer, AdminVerificationReviewSerializer
from authentication.permissions import IsActiveOrPendingVerification


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
    permission_classes = [IsActiveOrPendingVerification]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        # Vérifier si une demande existe déjà
        if hasattr(user, 'identity_request'):
            req = user.identity_request
            if req.status == 'PENDING':
                return Response(
                    {"detail": "Une demande est déjà en cours de traitement."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif req.status == 'APPROVED':
                return Response(
                    {"detail": "Votre identité est déjà vérifiée."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Si REJECTED, on permet de refaire une demande (on met à jour l'existant ou on en crée un nouveau)
            # Ici, on choisit de mettre à jour l'existant pour garder l'historique simple
            req.status = 'PENDING'
            req.rejection_reason = ""
            req.reviewed_by = None
            req.reviewed_at = None
            req.save()
            instance = req
        else:
            instance = None

        serializer = VerificationRequestSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            obj = serializer.save(user=user)
            return Response(
                {"message": "Documents soumis avec succès. En attente de validation par l'admin.", "id": obj.id},
                status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminReviewIdentityView(APIView):
    """
    Permet à un administrateur de valider ou rejeter une demande.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        verification_req = get_object_or_404(IdentityVerificationRequest, pk=pk)

        serializer = AdminVerificationReviewSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            action = data['action']

            if action == 'approve':
                verification_req.approve(request.user)
                # TODO: Envoyer un email de félicitations à l'utilisatrice
                return Response({"message": "Identité validée. Le compte a été activé."})

            elif action == 'reject':
                verification_req.reject(request.user, data.get('rejection_reason', ''))
                # TODO: Envoyer un email de rejet avec la raison
                return Response({"message": "Demande rejetée."})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)