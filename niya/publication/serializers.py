from rest_framework import serializers

from users.serializers import UserPreviewSerializer
from .models import Publication, Comment


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = ["id", "description", "media", "author", "created_at", "likes"]
        read_only_fields = ["author", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "description", "author", "created_at", "publication"]
        read_only_fields = ["author", "created_at", "publication"]
