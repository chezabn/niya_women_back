from django.contrib import admin

from .models import (
    Publication,
    PublicationMedia,
    PublicationLike,
    Comment,
)


class PublicationMediaInline(admin.TabularInline):
    model = PublicationMedia
    extra = 0
    readonly_fields = (
        "created_at",
    )

    fields = (
        "file",
        "media_type",
        "order",
        "created_at",
    )


class PublicationLikeInline(admin.TabularInline):
    model = PublicationLike
    extra = 0
    readonly_fields = (
        "user",
        "created_at",
    )

    can_delete = False

    fields = (
        "user",
        "created_at",
    )


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = (
        "author",
        "description",
        "created_at",
        "updated_at",
    )

    can_delete = False

    fields = (
        "author",
        "description",
        "created_at",
        "updated_at",
    )


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "caption_preview",
        "media_count",
        "likes_count",
        "comments_count",
        "comments_enabled",
        "is_archived",
        "is_edited",
        "created_at",
    )

    list_filter = (
        "is_archived",
        "comments_enabled",
        "is_edited",
        "created_at",
    )

    search_fields = (
        "author__username",
        "author__email",
        "caption",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [
        PublicationMediaInline,
        PublicationLikeInline,
        CommentInline,
    ]

    def caption_preview(self, obj):
        if len(obj.caption) <= 60:
            return obj.caption
        return obj.caption[:60] + "..."

    caption_preview.short_description = "Caption"

    def media_count(self, obj):
        return obj.medias.count()

    media_count.short_description = "Medias"

    def likes_count(self, obj):
        return obj.likes.count()

    likes_count.short_description = "Likes"

    def comments_count(self, obj):
        return obj.comments.count()

    comments_count.short_description = "Comments"


@admin.register(PublicationMedia)
class PublicationMediaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "publication",
        "media_type",
        "order",
        "created_at",
    )

    list_filter = (
        "media_type",
        "created_at",
    )

    search_fields = (
        "publication__author__username",
    )

    ordering = (
        "-created_at",
    )


@admin.register(PublicationLike)
class PublicationLikeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "publication",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "user__username",
        "publication__author__username",
    )

    ordering = (
        "-created_at",
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "publication",
        "description_preview",
        "created_at",
    )

    search_fields = (
        "author__username",
        "description",
    )

    list_filter = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def description_preview(self, obj):
        if len(obj.description) <= 60:
            return obj.description
        return obj.description[:60] + "..."

    description_preview.short_description = "Description"