from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from libs.permissions import (
    IsCommentOwner,
    IsFullyAuthenticated,
    IsPublicationOwner,
)
from notifications.models import Notification
from notifications.services import create_notification
from users.models import UserBlock

from .models import Comment, Publication, PublicationLike, PublicationReport
from .pagination import FeedPagination
from .serializers import (CommentSerializer, PublicationSerializer, PublicationLikeSerializer,
                          PublicationReportSerializer, PublicationReportDetailSerializer)


class PublicationViewSet(ModelViewSet):
    permission_classes = [
        IsFullyAuthenticated,
    ]

    serializer_class = PublicationSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        queryset = Publication.objects.filter(
            is_archived=False,
        )

        blocked_ids = UserBlock.objects.filter(
            Q(blocker=self.request.user) | Q(blocked=self.request.user)
        ).values_list("blocked_id", "blocker_id")

        hidden_ids = {pk for pair in blocked_ids for pk in pair}

        # Never hide the authenticated user's own publications.
        hidden_ids.discard(self.request.user.pk)

        queryset = queryset.exclude(author_id__in=hidden_ids)

        if self.action == "my_publications":
            queryset = queryset.filter(
                author=self.request.user,
            )
        elif self.action == "list":
            queryset = queryset.exclude(
                author=self.request.user,
            )

        return queryset.order_by("-created_at")

    def get_permissions(self):
        if self.action in [
            "update",
            "partial_update",
            "destroy",
            "my_detail",
        ]:
            return [
                IsFullyAuthenticated(),
                IsPublicationOwner(),
            ]

        return [
            IsFullyAuthenticated(),
        ]

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(
            is_edited=True,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="me",
    )
    def my_publications(self, request):
        publications = self.get_queryset()

        page = self.paginate_queryset(publications)

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
            )

            return self.get_paginated_response(
                serializer.data,
            )

        serializer = self.get_serializer(
            publications,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["GET"],
        url_path="me",
    )
    def my_detail(self, request, pk=None):
        publication = self.get_object()

        serializer = self.get_serializer(
            publication,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["GET"],
        url_path="comments",
    )
    def comments(self, request, pk=None):
        publication = self.get_object()

        comments = Comment.objects.filter(
            publication=publication,
        ).select_related(
            "author",
        ).order_by(
            "-created_at",
        )

        page = self.paginate_queryset(comments)

        if page is not None:
            serializer = CommentSerializer(
                page,
                many=True,
            )

            return self.get_paginated_response(
                serializer.data,
            )

        serializer = CommentSerializer(
            comments,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="liked",
    )
    def liked_publications(self, request):
        publications = self.get_queryset().filter(
            likes__user=request.user,
        ).distinct()

        page = self.paginate_queryset(publications)

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
            )

            return self.get_paginated_response(
                serializer.data,
            )

        serializer = self.get_serializer(
            publications,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path=r"user/(?P<user_id>[0-9]+)",
    )
    def user_publications(self, request, user_id=None):
        publications = self.get_queryset().filter(
            author_id=user_id,
        )

        page = self.paginate_queryset(publications)

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
            )

            return self.get_paginated_response(
                serializer.data,
            )

        serializer = self.get_serializer(
            publications,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class CommentViewSet(ModelViewSet):
    """
    CRUD operations for comments.
    """

    permission_classes = [
        IsFullyAuthenticated,
    ]

    serializer_class = CommentSerializer
    pagination_class = FeedPagination

    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
        "head",
        "options",
    ]

    def get_queryset(self):
        blocked_ids = UserBlock.objects.filter(
            Q(blocker=self.request.user) | Q(blocked=self.request.user)
        ).values_list("blocked_id", "blocker_id")
        hidden_ids = {pk for pair in blocked_ids for pk in pair}
        return Comment.objects.filter(
            publication__is_archived=False,
        ).exclude(author_id__in=hidden_ids).select_related(
            "author",
            "publication",
        ).order_by(
            "-created_at",
        )

    def get_permissions(self):
        if self.action in [
            "partial_update",
            "destroy",
        ]:
            return [
                IsFullyAuthenticated(),
                IsCommentOwner(),
            ]

        return [
            IsFullyAuthenticated(),
        ]

    def perform_create(self, serializer):
        comment = serializer.save(
            author=self.request.user,
        )
        create_notification(
            recipient=comment.publication.author,
            actor=self.request.user,
            notification_type=Notification.Type.COMMENT,
            publication=comment.publication,
        )


class PublicationLikeView(APIView):
    """
    Like or unlike a publication.

    POST:
        Create a like for the authenticated user.

    DELETE:
        Remove the authenticated user's like.
    """

    permission_classes = [
        IsFullyAuthenticated,
    ]

    def post(self, request, publication_id):
        publication = get_object_or_404(
            Publication,
            id=publication_id,
        )

        like, created = PublicationLike.objects.get_or_create(
            user=request.user,
            publication=publication,
        )

        serializer = PublicationLikeSerializer(
            like,
        )

        if not created:
            return Response(
                {
                    "detail": "Vous avez déjà aimé cette publication.",
                    "liked": True,
                    "like": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        create_notification(
            recipient=publication.author,
            actor=request.user,
            notification_type=Notification.Type.LIKE,
            publication=publication,
        )

        return Response(
            {
                "detail": "Publication aimée.",
                "liked": True,
                "like": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, publication_id):
        publication = get_object_or_404(
            Publication,
            id=publication_id,
        )

        deleted_count, _ = PublicationLike.objects.filter(
            user=request.user,
            publication=publication,
        ).delete()

        if deleted_count == 0:
            return Response(
                {
                    "detail": "Vous n'avez pas aimé cette publication.",
                    "liked": False,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "detail": "Like retiré.",
                "liked": False,
            },
            status=status.HTTP_200_OK,
        )


class PublicationReportView(APIView):
    permission_classes = [IsFullyAuthenticated]

    def post(self, request, publication_id):
        publication = get_object_or_404(Publication, pk=publication_id, is_archived=False)
        if publication.author_id == request.user.pk:
            return Response(
                {"detail": "Vous ne pouvez pas signaler votre propre publication."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PublicationReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        report = PublicationReport.objects.create(
            reporter=request.user,
            publication=publication,
            reason=serializer.validated_data["reason"],
        )
        staff_emails = list(
            get_user_model().objects.filter(is_staff=True).exclude(email="").values_list("email", flat=True)
        )
        if staff_emails:
            send_mail(
                subject="Nouveau signalement de publication sur Niya",
                message=(
                    f"Un signalement a été transmis par {request.user.username}.\n"
                    f"Publication : {publication.pk}, auteur : {publication.author.username}.\n"
                    f"Motif : {report.reason}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=staff_emails,
                fail_silently=True,
            )
        return Response(
            {"id": report.id, "detail": "Signalement transmis."},
            status=status.HTTP_201_CREATED,
        )


class AdminPublicationReportsView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = PublicationReportDetailSerializer
    pagination_class = FeedPagination
    queryset = PublicationReport.objects.select_related("reporter", "publication", "publication__author")
