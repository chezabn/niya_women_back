from rest_framework import serializers

from .models import Journal


class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = [
            "id",
            "title",
            "page",
            "date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Title cannot be empty."
            )
        return value

    def validate_page(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Page cannot be empty."
            )
        return value