from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from authentication.models import User


class AuthTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('register_api')
        self.login_url = reverse('login_api')
        self.users_url = reverse('users_api')

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "password2": "TestPass123",
            "first_name": "Test",
            "last_name": "User"
        }

        self.user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="password123"
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
        response = self.client.post(self.login_url, {
            "username": "existinguser",
            "password": "password123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_user_cant_login(self):
        response = self.client.post(self.login_url, {
            "username": "notExistingUser",
            "password": "password123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)