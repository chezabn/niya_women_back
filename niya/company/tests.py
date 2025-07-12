from django.contrib.auth import get_user_model
from .models import Company
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class CompanyAPITest(APITestCase):
    def setUp(self):
        self.company_url = reverse("company_api")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "password2": "TestPass123",
            "first_name": "Test",
            "last_name": "User",
        }

        self.user = User.objects.create_user(
            username="TestUser",
            email="usertest@example.com",
            password="password123",
        )

        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {self.token}"
        }

    def test_create_company_success(self):
        data = {
            "name": "Test Company",
            "description": "Company description",
        }
        response = self.client.post(self.company_url, data, format="json", **self.auth_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Company.objects.first().name, "Test Company")
        self.assertEqual(Company.objects.first().description, "Company description")

    def test_create_company_without_name_fails(self):
        data = {
            "description": "Missing name",
        }
        response = self.client.post(self.company_url, data, format="json", **self.auth_headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())

    def test_get_companies(self):
        Company.objects.create(user=self.user, name="Company1", description="desc")
        response = self.client.get(self.company_url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) >= 1)

