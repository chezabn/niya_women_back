from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import UserBlock
from .models import Follow


class FollowAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="one", email="one@example.com", password="StrongPass123!")
        self.target = User.objects.create_user(username="two", email="two@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)

    def test_follow_status_and_unfollow(self):
        url = reverse("follow-user", args=[self.target.pk])
        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertTrue(self.client.get(url).data["is_following"])
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Follow.objects.exists())

    def test_self_follow_missing_target_and_blocked_follow(self):
        self.assertEqual(self.client.post(reverse("follow-user", args=[self.user.pk])).status_code, 400)
        self.assertEqual(self.client.post(reverse("follow-user", args=[99999])).status_code, 404)
        UserBlock.objects.create(blocker=self.user, blocked=self.target)
        self.assertEqual(self.client.post(reverse("follow-user", args=[self.target.pk])).status_code, 403)

    def test_follower_and_following_lists(self):
        Follow.objects.create(follower=self.user, followed=self.target)
        self.assertEqual(self.client.get(reverse("user-followers", args=[self.target.pk])).data["count"], 1)
        self.assertEqual(self.client.get(reverse("user-following", args=[self.user.pk])).data["count"], 1)

    def test_follow_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("follow-user", args=[self.target.pk])).status_code, 401)
