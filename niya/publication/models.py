from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Publication(models.Model):
    description = models.CharField(max_length=255)
    media = models.CharField(max_length=100, blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="liked_publication", blank=True)

    def __str__(self):
        return self.description


class Comment(models.Model):
    description = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    publication = models.ForeignKey(
        Publication, on_delete=models.CASCADE, related_name="comments"
    )
    likes = models.ManyToManyField(User, related_name="liked_comment", blank=True)

    def __str__(self):
        return self.description
