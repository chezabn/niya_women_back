from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_id = serializers.IntegerField(source="actor.id", read_only=True)
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    publication_id = serializers.IntegerField(
        source="publication.id", read_only=True, allow_null=True
    )
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "actor_id",
            "actor_username",
            "publication_id",
            "created_at",
            "read_at",
            "is_read",
        ]

    def get_is_read(self, obj):
        return obj.read_at is not None
