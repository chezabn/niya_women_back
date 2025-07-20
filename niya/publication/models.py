from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Publication(models.Model):
    description = models.CharField(max_length=255)
    media = models.CharField(max_length=100, blank=True, null=True)
    author = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
