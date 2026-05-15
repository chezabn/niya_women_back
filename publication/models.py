from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Publication(models.Model):
    """
    Represents a user publication.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="publications",
    )

    caption = models.TextField(
        max_length=2200,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_edited = models.BooleanField(
        default=False,
    )

    comments_enabled = models.BooleanField(
        default=True,
    )

    is_archived = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Publication {self.pk}"


class PublicationMedia(models.Model):
    """
    Represents a media attached to a publication.
    """

    class MediaType(models.TextChoices):
        IMAGE = "IMAGE", "Image"
        VIDEO = "VIDEO", "Video"

    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name="medias",
    )

    file = models.FileField(
        upload_to="publications/",
    )

    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return f"{self.media_type} " f"for publication {self.publication_id}"


class PublicationLike(models.Model):
    """
    Represents a like on a publication.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="publication_likes",
    )

    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        unique_together = ("user", "publication")

        indexes = [
            models.Index(fields=["publication"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} likes " f"publication {self.publication_id}"


class Comment(models.Model):
    """
    Represents a comment on a publication.
    """

    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    description = models.TextField(
        max_length=1000,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Comment {self.pk}"
