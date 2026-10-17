from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Notification


class NotificationAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.recipient = User.objects.create_user(
            username="recipient",
            email="recipient@example.com",
            password="StrongPass123!",
            identity_verified=True,
            email_verified=True,
        )
        self.actor = User.objects.create_user(
            username="actor",
            email="actor@example.com",
            password="StrongPass123!",
            identity_verified=True,
            email_verified=True,
        )
        self.other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPass123!",
            identity_verified=True,
            email_verified=True,
        )
        self.unread = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            notification_type=Notification.Type.FOLLOW,
        )
        self.read = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            notification_type=Notification.Type.IDENTITY_APPROVED,
            read_at="2026-01-01T12:00:00Z",
        )
        self.foreign = Notification.objects.create(
            recipient=self.other,
            actor=self.actor,
            notification_type=Notification.Type.FOLLOW,
        )
        self.client.force_authenticate(self.recipient)

    def test_list_only_returns_recipient_notifications_and_filters_read_state(self):
        response = self.client.get(reverse("notifications-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        results = response.data["results"]
        self.assertEqual(
            {item["id"] for item in results}, {self.unread.pk, self.read.pk}
        )
        unread_response = self.client.get(
            reverse("notifications-list") + "?unread=true"
        )
        read_response = self.client.get(reverse("notifications-list") + "?unread=false")
        self.assertEqual(
            [item["id"] for item in unread_response.data["results"]], [self.unread.pk]
        )
        self.assertEqual(
            [item["id"] for item in read_response.data["results"]], [self.read.pk]
        )

    def test_read_single_and_all_are_idempotent_and_private(self):
        url = reverse("notification-read", args=[self.unread.pk])
        self.assertEqual(self.client.patch(url).status_code, 200)
        self.unread.refresh_from_db()
        self.assertIsNotNone(self.unread.read_at)
        self.assertEqual(self.client.patch(url).data, {"is_read": True})

        self.assertEqual(
            self.client.patch(
                reverse("notification-read", args=[self.foreign.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse("notifications-read-all")).data, {"updated": 0}
        )

        another = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            notification_type=Notification.Type.COMMENT,
        )
        self.assertEqual(
            self.client.post(reverse("notifications-read-all")).data, {"updated": 1}
        )
        another.refresh_from_db()
        self.assertIsNotNone(another.read_at)

    def test_delete_is_private_and_returns_not_found_for_missing_item(self):
        self.assertEqual(
            self.client.delete(
                reverse("notification-delete", args=[self.foreign.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(
                reverse("notification-delete", args=[self.unread.pk])
            ).status_code,
            204,
        )
        self.assertFalse(Notification.objects.filter(pk=self.unread.pk).exists())

    def test_endpoints_require_fully_verified_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.get(reverse("notifications-list")).status_code, 401
        )

        User = get_user_model()
        unverified = User.objects.create_user(
            username="unverified",
            email="unverified@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(unverified)
        self.assertEqual(
            self.client.get(reverse("notifications-list")).status_code, 403
        )
