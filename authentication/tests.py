from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from libs.errors import (
    INVALID_CODE,
    MISSING_CODE,
    MISSING_EMAIL,
    EMAIL_VERIFIED,
    SUCCESSFUL_EMAIL,
    PASSWORD_CHANGED,
    MISSING_INFORMATION,
    PASSWORD_NOT_SECURED,
    USER_OR_CODE_NOT_MATCH,
)
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

    def test_register_success(self):
        response = self.client.post(self.url, self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        self.assertTrue(User.objects.filter(username="testuser").exists())

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

    def test_login_account_will_locked(self):
        valid_payload = {
            "username": "testuser",
            "password": "False",
        }
        user = User.objects.get(username="testuser")
        user.failed_login_attempts = 4
        user.save()
        response = self.client.post(self.url, valid_payload)
        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        self.assertIn("detail", response.data)
        self.assertTrue(user.is_account_locked())
        assert user.failed_login_attempts == 5

    def test_login_wrong_password(self):
        valid_payload = {
            "username": "testuser",
            "password": "False",
        }
        response = self.client.post(self.url, valid_payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        user = User.objects.get(username="testuser")
        assert user.failed_login_attempts == 1


class SendVerificationCodeTests(APITestCase):
    def setUp(self):
        self.url = reverse("send_verification_code")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_send_verification_code_email_already_verified(self):
        self.user.email_verified = True
        self.user.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], EMAIL_VERIFIED)

    def test_send_verification_code_no_email(self):
        self.user.email = ""
        self.user.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MISSING_EMAIL)

    def test_send_verification_code_unauthenticated(self):
        self.client.credentials()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_send_verification_code_success(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_verification_code)
        self.assertIsNotNone(self.user.email_verification_code_expires)


class VerifyEmailTests(APITestCase):
    def setUp(self):
        self.url = reverse("verify_email")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )
        self.user.email_verification_code = "123456"
        self.user.email_verification_code_expires = timezone.now() + timezone.timedelta(
            minutes=15
        )
        self.user.save()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_verify_email_success(self):
        payload = {"code": "123456"}
        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], SUCCESSFUL_EMAIL)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertIsNone(self.user.email_verification_code)
        self.assertIsNone(self.user.email_verification_code_expires)

    def test_verify_email_no_code(self):
        payload = {}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MISSING_CODE)

    def test_verify_email_invalid_code(self):
        payload = {"code": "000000"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], INVALID_CODE)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_verify_email_expired_code(self):
        self.user.email_verification_code_expires = timezone.now() - timezone.timedelta(
            minutes=1
        )
        self.user.save()
        payload = {"code": "123456"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], INVALID_CODE)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_verify_email_unauthenticated(self):
        self.client.credentials()
        payload = {"code": "123456"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RequestPasswordResetTests(APITestCase):
    def setUp(self):
        self.url = reverse("request_password_reset")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )

    def test_request_password_reset_success_existing_email(self):
        payload = {"email": "test@example.com"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_code)
        self.assertIsNotNone(self.user.password_reset_code_expires)

    def test_request_password_reset_success_non_existing_email(self):
        payload = {"email": "unknown@example.com"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_request_password_reset_missing_email(self):
        payload = {}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MISSING_EMAIL)


class ConfirmPasswordResetTests(APITestCase):
    def setUp(self):
        self.url = reverse("confirm_password_reset")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="OldPassword123!",
        )
        self.user.password_reset_code = "123456"
        self.user.password_reset_code_expires = timezone.now() + timezone.timedelta(
            minutes=30
        )
        self.user.failed_login_attempts = 5
        self.user.locked_until = timezone.now() + timezone.timedelta(minutes=10)
        self.user.save()

    def test_confirm_password_reset_success(self):
        payload = {
            "email": "test@example.com",
            "code": "123456",
            "new_password": "NewStrongPassword123!",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], PASSWORD_CHANGED)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPassword123!"))
        self.assertIsNone(self.user.password_reset_code)
        self.assertIsNone(self.user.password_reset_code_expires)
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertIsNone(self.user.locked_until)

    def test_confirm_password_reset_missing_fields(self):
        payload = {
            "email": "test@example.com",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MISSING_INFORMATION)

    def test_confirm_password_reset_password_too_short(self):
        payload = {
            "email": "test@example.com",
            "code": "123456",
            "new_password": "123",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], PASSWORD_NOT_SECURED)

    def test_confirm_password_reset_user_not_found(self):
        payload = {
            "email": "unknown@example.com",
            "code": "123456",
            "new_password": "NewStrongPassword123!",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], USER_OR_CODE_NOT_MATCH)

    def test_confirm_password_reset_invalid_code(self):
        payload = {
            "email": "test@example.com",
            "code": "000000",
            "new_password": "NewStrongPassword123!",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], INVALID_CODE)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("NewStrongPassword123!"))

    def test_confirm_password_reset_expired_code(self):
        self.user.password_reset_code_expires = timezone.now() - timezone.timedelta(
            minutes=1
        )
        self.user.save()
        payload = {
            "email": "test@example.com",
            "code": "123456",
            "new_password": "NewStrongPassword123!",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], INVALID_CODE)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("NewStrongPassword123!"))
