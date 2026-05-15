from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from libs.permissions import IsFullyAuthenticated, IsPublicationOwner
from .models import (
    Comment,
    Publication,
    PublicationLike,
)
from .pagination import FeedPagination

from .serializers import (
    CommentSerializer,
    PublicationCreateSerializer,
    PublicationDetailSerializer,
    PublicationFeedSerializer,
)


class PublicationViewSet(ModelViewSet):
    permission_classes = [IsFullyAuthenticated]

    pagination_class = FeedPagination

    queryset = (
        Publication.objects.select_related("author")
        .prefetch_related(
            "medias",
            "likes",
            "comments",
        )
        .all()
    )

    def get_permissions(self):
        if self.action in [
            "update",
            "partial_update",
            "destroy",
        ]:
            return [
                IsFullyAuthenticated(),
                IsPublicationOwner(),
            ]

        return [IsFullyAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return PublicationCreateSerializer

        if self.action == "retrieve":
            return PublicationDetailSerializer

        return PublicationFeedSerializer

    def get_serializer_context(self):
        return {
            "request": self.request,
        }

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(is_edited=True)

    @action(
        detail=True,
        methods=["POST"],
        url_path="like",
    )
    def like(self, request, pk=None):
        publication = self.get_object()

        like, created = PublicationLike.objects.get_or_create(
            user=request.user,
            publication=publication,
        )

        if not created:
            return Response(
                {"detail": "Already liked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Publication liked."},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["DELETE"],
        url_path="unlike",
    )
    def unlike(self, request, pk=None):
        publication = self.get_object()

        deleted_count, _ = PublicationLike.objects.filter(
            user=request.user,
            publication=publication,
        ).delete()

        if deleted_count == 0:
            return Response(
                {"detail": "Like not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"detail": "Publication unliked."},
            status=status.HTTP_204_NO_CONTENT,
        )


class CommentViewSet(ModelViewSet):
    permission_classes = [IsFullyAuthenticated]

    serializer_class = CommentSerializer

    queryset = Comment.objects.select_related(
        "author",
        "publication",
    ).all()

    def get_serializer_context(self):
        return {
            "request": self.request,
        }

    def perform_create(self, serializer):
        publication_id = self.kwargs.get("publication_pk")

        publication = get_object_or_404(
            Publication,
            pk=publication_id,
        )

        serializer.save(
            author=self.request.user,
            publication=publication,
        )
