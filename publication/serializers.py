from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Publication


User = get_user_model()


class PublicationAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
        ]


class PublicationSerializer(serializers.ModelSerializer):
    author = PublicationAuthorSerializer(
        read_only=True,
    )

    class Meta:
        model = Publication

        fields = [
            "id",
            "author",
            "caption",
            "created_at",
            "updated_at",
            "is_edited",
            "comments_enabled",
            "is_archived",
        ]

        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "is_edited",
        ]

    def validate_caption(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Caption cannot be empty."
            )

        return value