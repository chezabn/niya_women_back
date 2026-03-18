from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Follow

User = get_user_model()


class FollowAPITest(APITestCase):
    def setUp(self):
        # Création de 3 utilisateurs
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="pass123"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@example.com", password="pass123"
        )

        # Tokens JWT
        self.token1 = str(RefreshToken.for_user(self.user1).access_token)
        self.token2 = str(RefreshToken.for_user(self.user2).access_token)
        self.token3 = str(RefreshToken.for_user(self.user3).access_token)

        self.auth_headers1 = {"HTTP_AUTHORIZATION": f"Bearer {self.token1}"}
        self.auth_headers2 = {"HTTP_AUTHORIZATION": f"Bearer {self.token2}"}
        self.auth_headers3 = {"HTTP_AUTHORIZATION": f"Bearer {self.token3}"}

        # URLs
        self.follow_url = lambda user_id: reverse("follow-user", args=[user_id])
        self.followers_url = lambda user_id: reverse("user-followers", args=[user_id])
        self.following_url = lambda user_id: reverse("user-following", args=[user_id])

    # ===========================
    # TESTS : SUIVRE / NE PLUS SUIVRE
    # ===========================

    def test_follow_user_success(self):
        """User1 suit User2"""
        response = self.client.post(
            self.follow_url(self.user2.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Follow.objects.filter(follower=self.user1, followed=self.user2).exists()
        )

    def test_follow_user_already_following(self):
        """Essayer de suivre une deuxième fois → 200 OK"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        response = self.client.post(
            self.follow_url(self.user2.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Follow.objects.count(), 1)

    def test_follow_self_forbidden(self):
        """Impossible de se suivre soi-même"""
        response = self.client.post(
            self.follow_url(self.user1.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, followed=self.user1).exists()
        )

    def test_unfollow_user_success(self):
        """User1 arrête de suivre User2"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        response = self.client.delete(
            self.follow_url(self.user2.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, followed=self.user2).exists()
        )

    def test_unfollow_user_not_following(self):
        """Ne pas suivre → suppression silencieuse (204)"""
        response = self.client.delete(
            self.follow_url(self.user2.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_follow_nonexistent_user(self):
        """Suivre un utilisateur qui n'existe pas → 404"""
        response = self.client.post(self.follow_url(9999), **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ===========================
    # TESTS : LISTE DES FOLLOWERS / FOLLOWING
    # ===========================

    def test_get_followers(self):
        """User2 est suivi par User1 et User3 → liste de 2 followers"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        Follow.objects.create(follower=self.user3, followed=self.user2)

        response = self.client.get(
            self.followers_url(self.user2.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        usernames = {user["username"] for user in response.data}
        self.assertIn("user1", usernames)
        self.assertIn("user3", usernames)

    def test_get_following(self):
        """User1 suit User2 et User3 → liste de 2 suivis"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        Follow.objects.create(follower=self.user1, followed=self.user3)

        response = self.client.get(
            self.following_url(self.user1.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        usernames = {user["username"] for user in response.data}
        self.assertIn("user2", usernames)
        self.assertIn("user3", usernames)

    def test_get_followers_empty(self):
        """Aucun follower → liste vide"""
        response = self.client.get(
            self.followers_url(self.user2.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_following_empty(self):
        """Ne suit personne → liste vide"""
        response = self.client.get(
            self.following_url(self.user1.id), **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # ===========================
    # TESTS : VÉRIFICATION DE L'ÉTAT (GET sur /follow/{id}/)
    # ===========================

    def test_check_if_following_true(self):
        """Vérifie qu'on suit bien l'utilisateur"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        response = self.client.get(self.follow_url(self.user2.id), **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_following"])

    def test_check_if_following_false(self):
        """Vérifie qu'on ne suit pas l'utilisateur"""
        response = self.client.get(self.follow_url(self.user2.id), **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_following"])

    # ===========================
    # TESTS : PERMISSIONS & SÉCURITÉ
    # ===========================

    def test_follow_without_auth(self):
        """Tentative de suivre sans authentification → 401"""
        response = self.client.post(self.follow_url(self.user2.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_followers_without_auth(self):
        """Accès public aux followers → 401 (car IsAuthenticated)"""
        response = self.client.get(self.followers_url(self.user2.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
