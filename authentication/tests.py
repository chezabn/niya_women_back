from django.utils import timezone

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
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        self.assertTrue(User.objects.filter(username="testuser").exists())

    # ------------------------
    # FAILURE CASE: invalid data
    # ------------------------
    def test_register_missing_fields(self):
        payload = {"username": ""}

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data or response.data.keys())


class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("login_api")
        self.valid_payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "first_name": "test",
            "last_name": "test",
            "accept_cgu": True,
        }
        _ = self.client.post(reverse("register_api"), self.valid_payload)

    def test_login_username_does_not_exist(self):
        payload = {
            "username": "unExistingUser",
            "password": "Test123!",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_user_locked(self):
        payload = {
            "username": "testuser",
            "password": "StrongPassword123!",
        }
        user = User.objects.get(username=payload["username"])
        user.locked_until = timezone.now() + timezone.timedelta(minutes=10)
        user.save()
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        self.assertIn("locked_until", response.data)
        self.assertIn("detail", response.data)

    def test_login_is_not_active(self):
        payload = {
            "username": "testuser",
            "password": "StrongPassword123!",
        }
        user = User.objects.get(username=payload["username"])
        user.is_active = False
        user.email_verified = True
        user.identity_verified = True
        user.save()
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)

    def test_login_success(self):
        valid_payload = {
            "username": "testuser",
            "password": "StrongPassword123!",
        }
        response = self.client.post(self.url, valid_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(username="testuser").exists())
        user = User.objects.get(username="testuser")
        assert user.failed_login_attempts == 0
        assert user.is_active

    def test_login_false_password(self):
        valid_payload = {
            "username": "testuser",
            "password": "False",
        }
        response = self.client.post(self.url, valid_payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        user = User.objects.get(username="testuser")
        assert user.failed_login_attempts == 1
