from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class HealthcheckTest(APITestCase):
    def test_healthcheck(self):
        response = self.client.get(reverse("healthcheck_auth_api"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("name", response.data)


class RegisterTests(APITestCase):
    def setUp(self):
        self.url = reverse("register_api")

        self.valid_payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "first_name": "test",
            "last_name": "test",
            "accept_cgu": True,
        }

    # ------------------------
    # SUCCESS CASE
    # ------------------------
    def test_register_success(self):
        response = self.client.post(self.url, self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)

        self.assertTrue(User.objects.filter(username="testuser").exists())

    # ------------------------
    # FAILURE CASE: invalid data
    # ------------------------
    def test_register_missing_fields(self):
        payload = {"username": ""}

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data or response.data.keys())
