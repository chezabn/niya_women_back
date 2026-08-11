from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Journal(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="journals",
    )

    title = models.CharField(
        max_length=255,
    )

    page = models.TextField()

    date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["author", "-date"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.date})"