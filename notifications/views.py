from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from libs.permissions import IsFullyAuthenticated
from publication.pagination import FeedPagination

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(ListAPIView):
    permission_classes = [IsFullyAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user).select_related(
            "actor", "publication"
        )
        unread = self.request.query_params.get("unread")
        if unread == "true":
            queryset = queryset.filter(read_at__isnull=True)
        elif unread == "false":
            queryset = queryset.filter(read_at__isnull=False)
        return queryset


class NotificationReadView(APIView):
    permission_classes = [IsFullyAuthenticated]

    def patch(self, request, notification_id):
        updated = Notification.objects.filter(
            pk=notification_id,
            recipient=request.user,
            read_at__isnull=True,
        ).update(read_at=timezone.now())
        if not updated and not Notification.objects.filter(
            pk=notification_id, recipient=request.user
        ).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({"is_read": True}, status=status.HTTP_200_OK)


class NotificationReadAllView(APIView):
    permission_classes = [IsFullyAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, read_at__isnull=True
        ).update(read_at=timezone.now())
        return Response({"updated": updated}, status=status.HTTP_200_OK)
