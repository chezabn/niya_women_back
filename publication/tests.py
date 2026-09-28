from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Comment, Publication, PublicationLike


class PublicationAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="author", email="author@example.com", password="StrongPass123!", identity_verified=True, email_verified=True)
        self.reader = User.objects.create_user(username="reader", email="reader@example.com", password="StrongPass123!", identity_verified=True, email_verified=True)
        self.client.force_authenticate(self.user)
        self.url = reverse("publications-list")

    def test_publication_crud_feed_pagination_and_author_rules(self):
        response = self.client.post(self.url, {"caption": "Hello"})
        self.assertEqual(response.status_code, 201)
        publication = Publication.objects.get()
        self.assertEqual(publication.author, self.user)
        feed = self.client.get(self.url)
        self.assertEqual(feed.data["count"], 0)  # own posts are served by /me/
        own_feed = self.client.get(reverse("publications-my-publications"))
        self.assertEqual(own_feed.data["count"], 1)
        detail = reverse("publications-detail", args=[publication.pk])
        self.assertEqual(self.client.patch(detail, {"caption": "Edited"}).status_code, 200)
        publication.refresh_from_db()
        self.assertTrue(publication.is_edited)
        self.assertEqual(self.client.delete(detail).status_code, 204)

    def test_like_and_comment_endpoints(self):
        self.client.force_authenticate(self.reader)
        publication = Publication.objects.create(author=self.user, caption="Open")
        like_url = reverse("publication-like", args=[publication.pk])
        self.assertEqual(self.client.post(like_url).status_code, 201)
        self.assertEqual(self.client.post(like_url).status_code, 200)
        self.assertEqual(self.client.delete(like_url).status_code, 200)
        response = self.client.post(reverse("comments-list"), {"publication": publication.pk, "description": "Nice"})
        self.assertEqual(response.status_code, 201)
        comment = Comment.objects.get()
        self.assertEqual(comment.author, self.reader)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.delete(reverse("comments-detail", args=[comment.pk])).status_code, 403)

    def test_comment_validation_and_full_authentication(self):
        publication = Publication.objects.create(author=self.user, caption="Closed", comments_enabled=False)
        self.assertEqual(self.client.post(reverse("comments-list"), {"publication": publication.pk, "description": "Text"}).status_code, 400)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_authenticate(self.reader)
        self.assertEqual(PublicationLike.objects.count(), 0)
