from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Friendship

User = get_user_model()


class FollowStatusSerializer(serializers.Serializer):
    is_following = serializers.BooleanField()


class FriendshipStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Friendship.STATUS_CHOICES,
        allow_null=True,
    )


class FriendTargetSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def validate_user_id(self, target_user):
        request = self.context["request"]
        if target_user == request.user:
            raise serializers.ValidationError("You cannot add yourself")
        return target_user
