from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Publication, Comment

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

class CommentAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
        ]

class CommentSerializer(serializers.ModelSerializer):
    author = CommentAuthorSerializer(
        read_only=True,
    )

    class Meta:
        model = Comment

        fields = [
            "id",
            "publication",
            "author",
            "description",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "author",
            "created_at",
        ]

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Comment cannot be empty."
            )

        return value

    def validate_publication(self, value):
        if not value.comments_enabled:
            raise serializers.ValidationError(
                "Comments are disabled for this publication."
            )

        if value.is_archived:
            raise serializers.ValidationError(
                "You cannot comment on an archived publication."
            )

        return value