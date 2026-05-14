from rest_framework import serializers

from users.serializers import UserPreviewSerializer

from .models import (
    Comment,
    Publication,
    PublicationLike,
    PublicationMedia,
)


class PublicationMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationMedia

        fields = [
            "id",
            "file",
            "media_type",
            "order",
        ]


class PublicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication

        fields = [
            "id",
            "caption",
            "comments_enabled",
        ]

    def validate_caption(
        self,
        value: str,
    ) -> str:
        if not value.strip():
            raise serializers.ValidationError("Caption cannot be empty.")

        return value


class PublicationFeedSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer(
        read_only=True,
    )

    medias = PublicationMediaSerializer(
        many=True,
        read_only=True,
    )

    likes_count = serializers.SerializerMethodField()

    comments_count = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Publication

        fields = [
            "id",
            "author",
            "caption",
            "medias",
            "likes_count",
            "comments_count",
            "is_liked",
            "is_edited",
            "created_at",
        ]

    def get_likes_count(
        self,
        obj: Publication,
    ) -> int:
        return obj.likes.count()

    def get_comments_count(
        self,
        obj: Publication,
    ) -> int:
        return obj.comments.count()

    def get_is_liked(
        self,
        obj: Publication,
    ) -> bool:
        request = self.context.get("request")

        if not request:
            return False

        return obj.likes.filter(user=request.user).exists()


class PublicationDetailSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer(
        read_only=True,
    )

    medias = PublicationMediaSerializer(
        many=True,
        read_only=True,
    )

    likes_count = serializers.SerializerMethodField()

    comments_count = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Publication

        fields = [
            "id",
            "author",
            "caption",
            "medias",
            "likes_count",
            "comments_count",
            "is_liked",
            "comments_enabled",
            "created_at",
            "updated_at",
            "is_edited",
        ]

    def get_likes_count(
        self,
        obj: Publication,
    ) -> int:
        return obj.likes.count()

    def get_comments_count(
        self,
        obj: Publication,
    ) -> int:
        return obj.comments.count()

    def get_is_liked(
        self,
        obj: Publication,
    ) -> bool:
        request = self.context.get("request")

        if not request:
            return False

        return obj.likes.filter(user=request.user).exists()


class PublicationLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationLike

        fields = [
            "id",
            "user",
            "publication",
            "created_at",
        ]


class CommentSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer(
        read_only=True,
    )

    class Meta:
        model = Comment

        fields = [
            "id",
            "description",
            "author",
            "created_at",
        ]
