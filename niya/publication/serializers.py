from rest_framework import serializers

from .models import User, Publication


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = ["id", "description", "media", "author", "created_at", "likes"]
        read_only_fields = ["author", "created_at"]
