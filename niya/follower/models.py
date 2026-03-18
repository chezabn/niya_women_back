from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Follow(models.Model):
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )
    followed = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "followed")
        constraints = [
            models.CheckConstraint(
                check=~models.Q(follower=models.F("followed")),
                name="prevent_self_follow",
            )
        ]

    def __str__(self):
        return f"{self.follower} follows {self.followed}"
