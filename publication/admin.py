from django.contrib import admin

from .models import Comment, Publication, PublicationLike


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "caption_preview",
        "comments_enabled",
        "is_archived",
        "is_edited",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "comments_enabled",
        "is_archived",
        "is_edited",
        "created_at",
    )

    search_fields = (
        "caption",
        "author__username",
        "author__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="Caption")
    def caption_preview(self, obj):
        if len(obj.caption) > 60:
            return f"{obj.caption[:60]}..."
        return obj.caption


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
        "user__email",
        "publication__caption",
    )

    readonly_fields = (
        "created_at",
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

    list_filter = (
        "created_at",
    )

    search_fields = (
        "description",
        "author__username",
        "author__email",
        "publication__caption",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="Description")
    def description_preview(self, obj):
        if len(obj.description) > 60:
            return f"{obj.description[:60]}..."
        return obj.description