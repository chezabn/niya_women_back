from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Journal


class JournalAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="writer", email="writer@example.com", password="StrongPass123!",
            is_active=True, identity_verified=True, email_verified=True,
        )
        self.other = get_user_model().objects.create_user(
            username="other", email="other@example.com", password="StrongPass123!",
            is_active=True, identity_verified=True, email_verified=True,
        )
        self.client.force_authenticate(self.user)
        self.url = reverse("journals-list")

    def test_create_list_update_and_delete_own_journal(self):
        payload = {"title": "Today", "page": "A good day", "date": "2026-09-28"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 201)
        journal_id = response.data["id"]
        self.assertEqual(self.client.get(self.url).data["results"][0]["title"], "Today")
        detail = reverse("journals-detail", args=[journal_id])
        self.assertEqual(self.client.patch(detail, {"title": "Updated"}).data["title"], "Updated")
        self.assertEqual(self.client.delete(detail).status_code, 204)

    def test_journal_is_private_and_empty_title_is_rejected(self):
        entry = Journal.objects.create(author=self.other, title="Private", page="Text", date=date.today())
        self.assertEqual(self.client.get(reverse("journals-detail", args=[entry.pk])).status_code, 404)
        self.assertEqual(self.client.post(self.url, {"title": " ", "page": "Text", "date": "2026-09-28"}).status_code, 400)

    def test_journal_requires_fully_verified_user(self):
        self.client.force_authenticate(get_user_model().objects.create_user(
            username="unverified", email="unverified@example.com", password="StrongPass123!"
        ))
        self.assertEqual(self.client.get(self.url).status_code, 403)
