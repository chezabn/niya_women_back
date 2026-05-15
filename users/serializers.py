from django.contrib.auth import get_user_model
from rest_framework import serializers

from libs.errors import EMAIL_ALREADY_REGISTERED
from .models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["bio"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "identity_verified",
            "profile",
        ]


class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    email = serializers.EmailField(required=False)
    bio = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError(EMAIL_ALREADY_REGISTERED)

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)
        instance.save()
        profile, created = UserProfile.objects.get_or_create(user=instance)
        profile.bio = validated_data.get("bio", profile.bio)
        profile.save()
        return instance


class UserPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "identity_verified", "profile"]
