from django.shortcuts import get_object_or_404
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

from .models import Comment, Publication, PublicationLike
from .pagination import FeedPagination
from .serializers import CommentSerializer, PublicationSerializer, PublicationLikeSerializer


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

        if self.action == "my_publications":
            queryset = queryset.filter(
                author=self.request.user,
            )
        elif self.action == "list":
            queryset = queryset.exclude(
                author=self.request.user,
            )

        return queryset.order_by(
            "-created_at",
        )

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
        return Comment.objects.filter(
            publication__is_archived=False,
        ).select_related(
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
        serializer.save(
            author=self.request.user,
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