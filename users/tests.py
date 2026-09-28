from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import UserBlock, UserReport, UserProfile


class UsersAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="me", email="me@example.com", password="StrongPass123!", identity_verified=True, email_verified=True)
        self.other = User.objects.create_user(username="other", email="other@example.com", password="StrongPass123!", identity_verified=True, email_verified=True)
        self.client.force_authenticate(self.user)

    def test_profile_read_update_and_blocking(self):
        self.assertEqual(self.client.get(reverse("my_user")).status_code, 200)
        response = self.client.patch(reverse("my_user"), {"bio": "Hello", "first_name": "Ada"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfile.objects.get(user=self.user).bio, "Hello")
        block_url = reverse("user_block", args=[self.other.pk])
        self.assertEqual(self.client.post(block_url).status_code, 201)
        self.assertEqual(self.client.get(reverse("blocked_users")).data["count"], 1)
        self.assertEqual(self.client.delete(block_url).status_code, 204)
        self.assertFalse(UserBlock.objects.exists())

    def test_search_detail_and_report(self):
        self.assertEqual(self.client.get(reverse("search_user") + "?search=oth").status_code, 200)
        self.assertEqual(self.client.get(reverse("user_detail", args=[self.other.pk])).status_code, 200)
        response = self.client.post(reverse("user_report"), {"user_id": self.other.pk, "reason": "Abuse"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(UserReport.objects.get().reason, "Abuse")
        self.assertEqual(self.client.post(reverse("user_report"), {"user_id": self.user.pk, "reason": "Self"}).status_code, 400)

    def test_user_endpoints_require_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("my_user")).status_code, 401)
