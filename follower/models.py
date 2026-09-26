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


class Friendship(models.Model):
    PENDING = "pending"
    ACCEPTED = "accepted"
    STATUS_CHOICES = [(PENDING, "Pending"), (ACCEPTED, "Accepted")]

    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_requests_sent"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_requests_received"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["requester", "recipient"], name="unique_friend_request"
            ),
            models.CheckConstraint(
                condition=~models.Q(requester=models.F("recipient")),
                name="prevent_self_friendship",
            ),
        ]

    def __str__(self):
        return f"{self.requester} → {self.recipient} ({self.status})"
