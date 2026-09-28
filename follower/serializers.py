from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class FollowStatusSerializer(serializers.Serializer):
    is_following = serializers.BooleanField()

