from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from libs.permissions import (
    IsFullyAuthenticated,
    IsPublicationOwner,
)

from .models import (
    Comment,
    Publication,
    PublicationLike,
    PublicationMedia,
)

from .pagination import FeedPagination

from .serializers import (
    CommentSerializer,
    PublicationCreateSerializer,
    PublicationDetailSerializer,
    PublicationFeedSerializer,
)


class PublicationViewSet(ModelViewSet):
    permission_classes = [
        IsFullyAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    pagination_class = FeedPagination

    queryset = (
        Publication.objects
        .select_related("author")
        .prefetch_related(
            "medias",
            "likes",
            "comments",
        )
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

        return [
            IsFullyAuthenticated(),
        ]

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

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = PublicationCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        files = serializer.validated_data.pop(
            "files",
            [],
        )

        publication = serializer.save(
            author=request.user,
        )

        for index, file in enumerate(files):
            content_type = getattr(
                file,
                "content_type",
                "",
            )

            media_type = (
                PublicationMedia.MediaType.VIDEO
                if content_type.startswith("video/")
                else PublicationMedia.MediaType.IMAGE
            )

            PublicationMedia.objects.create(
                publication=publication,
                file=file,
                media_type=media_type,
                order=index,
            )

        return Response(
            PublicationDetailSerializer(
                publication,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(
        self,
        serializer,
    ):
        serializer.save(
            is_edited=True,
        )

    @action(
        detail=True,
        methods=["POST"],
        url_path="like",
    )
    def like(self, request, pk=None):
        publication = self.get_object()

        like, created = (
            PublicationLike.objects.get_or_create(
                user=request.user,
                publication=publication,
            )
        )

        if not created:
            return Response(
                {
                    "detail": "Already liked."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Publication liked."
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["DELETE"],
        url_path="unlike",
    )
    def unlike(self, request, pk=None):
        publication = self.get_object()

        deleted_count, _ = (
            PublicationLike.objects.filter(
                user=request.user,
                publication=publication,
            ).delete()
        )

        if deleted_count == 0:
            return Response(
                {
                    "detail": "Like not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "detail": "Publication unliked."
            },
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="me",
    )
    def me(self, request):
        queryset = (
            self.get_queryset()
            .filter(
                author=request.user,
                is_archived=False,
            )
            .order_by("-created_at")
        )

        page = self.paginate_queryset(
            queryset,
        )

        if page is not None:
            serializer = PublicationFeedSerializer(
                page,
                many=True,
                context=self.get_serializer_context(),
            )

            return self.get_paginated_response(
                serializer.data,
            )

        serializer = PublicationFeedSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class CommentViewSet(ModelViewSet):
    permission_classes = [
        IsFullyAuthenticated,
    ]

    serializer_class = CommentSerializer

    def get_queryset(self):
        publication_id = self.kwargs.get(
            "publication_pk",
        )

        return (
            Comment.objects
            .select_related(
                "author",
                "publication",
            )
            .filter(
                publication_id=publication_id,
            )
        )

    def get_serializer_context(self):
        return {
            "request": self.request,
        }

    def perform_create(
        self,
        serializer,
    ):
        publication_id = self.kwargs.get(
            "publication_pk",
        )

        publication = get_object_or_404(
            Publication,
            pk=publication_id,
        )

        if not publication.comments_enabled:
            raise ValidationError(
                "Comments are disabled for this publication."
            )

        serializer.save(
            author=self.request.user,
            publication=publication,
        )