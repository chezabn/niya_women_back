import uuid
from datetime import datetime
from time import sleep

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse

from .models import Publication, Comment

User = get_user_model()


# Helper pour générer un email unique à chaque fois
def get_unique_email(prefix="test"):
    """Génère un email unique pour éviter les conflits UNIQUE constraint."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}@example.com"


class PublicationAPITest(APITestCase):
    def setUp(self):
        self.publications_url = reverse("publication")

        # Utilisation d'emails uniques
        self.user = User.objects.create_user(
            username="TestUser",
            email=get_unique_email("usertest"),
            password="password123",
        )

        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_create_publication(self):
        data = {"description": "My First Publication"}
        response = self.client.post(
            self.publications_url, data, format="json", **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Publication.objects.count(), 1)
        publication = Publication.objects.first()
        self.assertEqual(publication.description, data["description"])
        self.assertEqual(publication.author, self.user)

    def test_create_publication_with_invalid_data(self):
        data = {"media": "path/image.png"}
        response = self.client.post(
            self.publications_url, data, format="json", **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Publication.objects.count(), 0)

    def test_get_publication(self):
        data = {"description": "My First Publication"}
        self.client.post(
            self.publications_url, data, format="json", **self.auth_headers
        )
        response = self.client.get(self.publications_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Publication.objects.count(), 1)
        publication = Publication.objects.first()
        self.assertEqual(publication.description, "My First Publication")

    def test_patch_publication(self):
        data = {"description": "My First Publication"}
        response = self.client.post(
            self.publications_url, data, format="json", **self.auth_headers
        )
        publication_id = response.json()["id"]
        url = reverse("publication-detail", args=[publication_id])
        new_data = {"description": "My publication updated"}
        response = self.client.patch(url, new_data, format="json", **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_publication(self):
        data = {"description": "My First Publication"}
        response = self.client.post(
            self.publications_url, data, format="json", **self.auth_headers
        )
        publication_id = response.json()["id"]
        url = reverse("publication-detail", args=[publication_id])
        response = self.client.delete(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class PublicationLikeAPITest(APITestCase):
    def setUp(self):
        # Création d'utilisateurs avec emails uniques
        self.user1 = User.objects.create_user(
            username="TestUser1",
            email=get_unique_email("user1_like"),
            password="pass123",
        )
        self.token1 = str(RefreshToken.for_user(self.user1).access_token)
        self.auth_headers1 = {"HTTP_AUTHORIZATION": f"Bearer {self.token1}"}

        self.user2 = User.objects.create_user(
            username="TestUser2",
            email=get_unique_email("user2_like"),
            password="pass123",
        )
        self.token2 = str(RefreshToken.for_user(self.user2).access_token)
        self.auth_headers2 = {"HTTP_AUTHORIZATION": f"Bearer {self.token2}"}

        self.publication = Publication.objects.create(
            description="My First Publication",
            author=self.user1,
        )

        self.like_url = reverse("publication-like", args=[self.publication.id])
        self.comment_url = reverse("publication-comment", args=[self.publication.id])

    def test_like_publication(self):
        response = self.client.post(self.like_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2, self.publication.likes.all())

    def test_unlike_publication(self):
        response = self.client.post(self.like_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2, self.publication.likes.all())
        # Unlike post
        response = self.client.delete(self.like_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user2, self.publication.likes.all())

    def test_get_all_likes(self):
        response = self.client.post(self.like_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2, self.publication.likes.all())
        response = self.client.get(self.like_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [user["username"] for user in response.json()["users"]]
        self.assertIn(self.user2.username, usernames)


class PublicationCommentAPITest(APITestCase):
    def setUp(self):
        # Création d'utilisateurs avec emails uniques
        self.user1 = User.objects.create_user(
            username="TestUser1",
            email=get_unique_email("user1_comment"),
            password="pass123",
        )
        self.token1 = str(RefreshToken.for_user(self.user1).access_token)
        self.auth_headers1 = {"HTTP_AUTHORIZATION": f"Bearer {self.token1}"}

        self.user2 = User.objects.create_user(
            username="TestUser2",
            email=get_unique_email("user2_comment"),
            password="pass123",
        )
        self.token2 = str(RefreshToken.for_user(self.user2).access_token)
        self.auth_headers2 = {"HTTP_AUTHORIZATION": f"Bearer {self.token2}"}

        self.publication = Publication.objects.create(
            description="My First Publication",
            author=self.user1,
        )
        self.comment_list_url = reverse(
            "publication-comment", args=[self.publication.id]
        )

    def test_create_comment(self):
        data = {"description": "Great post!"}
        response = self.client.post(
            self.comment_list_url, data, format="json", **self.auth_headers2
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.description, "Great post!")
        self.assertEqual(comment.author, self.user2)
        self.assertEqual(comment.publication, self.publication)

    def test_get_comments(self):
        Comment.objects.create(
            author=self.user2,
            publication=self.publication,
            description="First comment",
            created_at=datetime.now(),
        )
        sleep(0.5)
        Comment.objects.create(
            author=self.user1,
            publication=self.publication,
            description="Second comment",
            created_at=datetime.now(),
        )

        response = self.client.get(self.comment_list_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Vérifie l'ordre (le plus récent en premier si trié ainsi)
        self.assertEqual(response.data[0]["description"], "Second comment")

    def test_update_own_comment(self):
        comment = Comment.objects.create(
            author=self.user2,
            publication=self.publication,
            description="Old comment",
            created_at=datetime.now(),
        )
        detail_url = reverse("comment-detail", args=[comment.id])
        new_data = {"description": "Updated comment"}

        response = self.client.patch(
            detail_url, new_data, format="json", **self.auth_headers2
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.description, "Updated comment")

    def test_update_other_user_comment_forbidden(self):
        comment = Comment.objects.create(
            author=self.user1,
            publication=self.publication,
            description="User1's comment",
            created_at=datetime.now(),
        )
        detail_url = reverse("comment-detail", args=[comment.id])
        new_data = {"description": "Hacked!"}

        response = self.client.patch(
            detail_url, new_data, format="json", **self.auth_headers2
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        comment.refresh_from_db()
        self.assertEqual(comment.description, "User1's comment")

    def test_delete_own_comment(self):
        comment = Comment.objects.create(
            author=self.user2,
            publication=self.publication,
            description="To delete",
            created_at=datetime.now(),
        )
        detail_url = reverse("comment-detail", args=[comment.id])

        response = self.client.delete(detail_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comment_as_publication_author(self):
        comment = Comment.objects.create(
            author=self.user2,
            publication=self.publication,
            description="Comment by user2",
            created_at=datetime.now(),
        )
        detail_url = reverse("comment-detail", args=[comment.id])

        response = self.client.delete(detail_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comment_as_other_user_forbidden(self):
        # Correction ici : utilisation d'un email unique pour user3 aussi
        user3 = User.objects.create_user(
            username="user3",
            email=get_unique_email("user3_forbidden"),
            password="pass123",
        )
        token3 = str(RefreshToken.for_user(user3).access_token)
        auth_headers3 = {"HTTP_AUTHORIZATION": f"Bearer {token3}"}

        comment = Comment.objects.create(
            author=self.user2,
            publication=self.publication,
            description="Protected comment",
            created_at=datetime.now(),
        )
        detail_url = reverse("comment-detail", args=[comment.id])

        response = self.client.delete(detail_url, **auth_headers3)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)

    def test_delete_nonexistent_comment(self):
        detail_url = reverse("comment-detail", args=[999])
        response = self.client.delete(detail_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
