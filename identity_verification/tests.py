from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import IdentityVerificationRequest


class IdentityVerificationAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.storage = IdentityVerificationRequest._meta.get_field("id_card_front").storage
        self.storage_save_patcher = patch.object(
            self.storage,
            "save",
            side_effect=lambda name, content, **kwargs: name,
        )
        self.storage_save_patcher.start()
        self.user = User.objects.create_user(username="member", email="member@example.com", password="StrongPass123!", is_active=False)
        self.admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="StrongPass123!")
        self.request_obj = IdentityVerificationRequest.objects.create(
            user=self.user,
            id_card_front=ContentFile(b"card", name="card.jpg"),
            selfie_with_id=ContentFile(b"selfie", name="selfie.jpg"),
        )

    def tearDown(self):
        self.storage_save_patcher.stop()

    def test_status_returns_request_or_empty_state(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("identity_verification_status"))
        self.assertTrue(response.data["has_request"])
        self.assertEqual(response.data["status"], "PENDING")

    @patch("identity_verification.views.send_mail")
    @patch("identity_verification.views.AdminReviewIdentityView.delete_verification_images")
    def test_admin_approval_updates_user_and_cleans_storage(self, delete_images, send_mail_mock):
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("admin_review_identity", args=[self.request_obj.pk]), {"action": "approve"})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.identity_verified)
        delete_images.assert_called_once()
        send_mail_mock.assert_called_once()

    @patch("identity_verification.views.send_mail")
    @patch("identity_verification.views.AdminReviewIdentityView.delete_verification_images")
    def test_admin_rejection_requires_reason_then_rejects_and_deletes(self, delete_images, send_mail_mock):
        self.client.force_authenticate(self.admin)
        url = reverse("admin_review_identity", args=[self.request_obj.pk])
        self.assertEqual(self.client.post(url, {"action": "reject"}).status_code, 400)
        response = self.client.post(url, {"action": "reject", "rejection_reason": "Image unclear"})
        self.assertEqual(response.status_code, 200)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, "REJECTED")
        delete_images.assert_called_once()
        send_mail_mock.assert_called_once()

    def test_admin_list_status_filter_pagination_and_permission(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("admin_identity_verification_list") + "?status=pending&page_size=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["status"], "PENDING")
        self.assertEqual(self.client.get(reverse("admin_identity_verification_list") + "?status=nope").status_code, 400)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(reverse("admin_identity_verification_list")).status_code, 403)

    def test_real_storage_cleanup_deletes_both_files_and_clears_names(self):
        with patch.object(self.storage, "delete") as delete_mock:
            # Each ImageField shares the configured storage, and each object key is removed.
            AdminView = __import__("identity_verification.views", fromlist=["AdminReviewIdentityView"]).AdminReviewIdentityView
            AdminView.delete_verification_images(self.request_obj)
        self.assertEqual(delete_mock.call_count, 2)
        self.request_obj.refresh_from_db()
        self.assertFalse(self.request_obj.id_card_front.name)
        self.assertFalse(self.request_obj.selfie_with_id.name)
