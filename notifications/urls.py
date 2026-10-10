from django.urls import path

from .views import NotificationListView, NotificationReadAllView, NotificationReadView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications-list"),
    path("read-all/", NotificationReadAllView.as_view(), name="notifications-read-all"),
    path("<int:notification_id>/read/", NotificationReadView.as_view(), name="notification-read"),
]
