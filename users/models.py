from django.db import models

from niya import settings


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(null=True, blank=True, default="")

    def __str__(self):
        return str(self.user.username)


class UserBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_blocks"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by_users"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("blocker", "blocked"), name="unique_user_block"),
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")),
                name="prevent_self_block",
            ),
        ]


class UserReport(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_reports_filed",
    )
    reported = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_reports_received",
    )
    reason = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(reporter=models.F("reported")),
                name="prevent_self_report",
            ),
        ]
