from django.db import models

from niya import settings


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(null=True, blank=True, default="")

    def __str__(self):
        return str(self.user.username)
