from datetime import datetime

from django.contrib.auth import get_user_model
from rest_framework import status

from .models import Publication
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class PublicationAPITest(APITestCase):
    def setUp(self):
        self.publications_url = reverse("publication")

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
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_create_publication(self):
        data = {
            "description": "My First Publication",
        }
        response = self.client.post(
            self.publications_url, data, format="json", **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Publication.objects.count(), 1)
        publication = Publication.objects.first()
        self.assertEqual(publication.description, data["description"])
        self.assertEqual(publication.author, self.user)

    def test_create_publication_with_invalid_data(self):
        data = {
            "media": "path/image.png",
        }
        response = self.client.post(
            self.publications_url, data, format="json", **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Publication.objects.count(), 0)

    def test_get_publication(self):
        data = {
            "description": "My First Publication",
        }
        response = self.client.post(
            self.publications_url, data, format="json", **self.auth_headers
        )
        response = self.client.get(self.publications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Publication.objects.count(), 1)
        publication = Publication.objects.first()
        self.assertEqual(publication.description, "My First Publication")