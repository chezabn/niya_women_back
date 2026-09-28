from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Company


class CompanyAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner", email="owner@example.com", password="StrongPass123!"
        )
        self.client.force_authenticate(self.user)

    def test_create_get_update_and_delete_company(self):
        url = reverse("my_company_api")
        payload = {"name": "Studio", "description": "Design"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Company.objects.get().user, self.user)
        self.assertEqual(self.client.get(url).data["name"], "Studio")
        self.assertEqual(self.client.patch(url, {"name": "New name"}).data["name"], "New name")
        self.assertEqual(self.client.delete(url, {"confirm": True}).status_code, 204)

    def test_company_requires_authentication_and_valid_fields(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(reverse("my_company_api")).status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(reverse("my_company_api"), {}).status_code, 400)

    def test_company_search_and_missing_detail(self):
        Company.objects.create(user=self.user, name="Atelier", description="Mode")
        self.assertEqual(len(self.client.get(reverse("company_api") + "?search=mode").data), 1)
        self.assertEqual(self.client.get(reverse("company_api_id", args=[999])).status_code, 404)
