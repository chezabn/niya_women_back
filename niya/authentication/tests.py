from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class AuthTests(APITestCase):

    def setUp(self):
        self.register_url = reverse("register_api")
        self.login_url = reverse("login_api")
        self.users_url = reverse("users_api")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "password2": "TestPass123",
            "first_name": "Test",
            "last_name": "User",
        }

        self.user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="password123",
        )

    # Test signup
    def test_user_signup(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.json())
        self.assertIn("refresh_token", response.json())
        self.assertIn("message", response.json())

    # Test login JWT
    def test_user_can_login(self):
        response = self.client.post(
            self.login_url,
            {"username": "existinguser", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_user_cant_login(self):
        response = self.client.post(
            self.login_url,
            {"username": "notExistingUser", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmailVerificationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        self.send_verification_url = reverse("send_verification_code")
        self.verify_email_url = reverse("verify_email")

    def test_send_verification_code(self):
        """Test l'envoi du code de vérification"""
        response = self.client.post(self.send_verification_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.user.refresh_from_db()
        # Vérifie qu'un e-mail a été "envoyé" (en dev, dans mail.outbox)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email_verification_code, mail.outbox[0].body)

    def test_verify_email_success(self):
        """Test la vérification avec un code valide"""
        # Génère un code
        self.user.generate_verification_code()
        code = self.user.email_verification_code

        response = self.client.post(
            self.verify_email_url, {"code": code}, **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_verify_email_invalid_code(self):
        """Test avec un code invalide"""
        self.user.generate_verification_code()
        response = self.client.post(
            self.verify_email_url, {"code": "000000"}, **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_verify_email_expired_code(self):
        """Test avec un code expiré"""
        self.user.generate_verification_code()
        self.user.email_verification_code_expires = timezone.now() - timezone.timedelta(
            minutes=1
        )
        self.user.save()

        response = self.client.post(
            self.verify_email_url,
            {"code": self.user.email_verification_code},
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_cannot_verify_already_verified_email(self):
        """Empêche de renvoyer un code si déjà vérifié"""
        self.user.email_verified = True
        self.user.save()
        response = self.client.post(self.send_verification_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
