from rest_framework.viewsets import ModelViewSet

from libs.permissions import IsFullyAuthenticated
from .models import Journal
from .serializers import JournalSerializer


class JournalViewSet(ModelViewSet):
    permission_classes = [
        IsFullyAuthenticated,
    ]

    serializer_class = JournalSerializer

    def get_queryset(self):
        return Journal.objects.filter(
            author=self.request.user
        ).order_by(
            "-date",
            "-created_at",
        )

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )