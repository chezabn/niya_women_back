from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from libs.permissions import IsFullyAuthenticated, IsPublicationOwner

from .models import Publication
from .serializers import PublicationSerializer


class PublicationViewSet(ModelViewSet):
    """
    CRUD and listing operations for publications.
    """

    permission_classes = [
        IsFullyAuthenticated,
    ]

    serializer_class = PublicationSerializer

    def get_queryset(self):
        return Publication.objects.filter(
            is_archived=False,
        ).order_by(
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
        publications = self.get_queryset().filter(
            author=request.user,
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
