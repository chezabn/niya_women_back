from django.contrib import admin

from .models import Comment, Publication, PublicationLike, PublicationReport


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


@admin.register(PublicationReport)
class PublicationReportAdmin(admin.ModelAdmin):
    list_display = ("id", "publication", "reported_author", "reporter", "reason_preview", "created_at")
    list_filter = ("created_at",)
    search_fields = ("publication__caption", "publication__author__username", "reporter__username", "reason")
    readonly_fields = ("publication", "reporter", "reason", "created_at")
    ordering = ("-created_at",)
    list_select_related = ("publication", "publication__author", "reporter")

    @admin.display(description="Auteur signalé")
    def reported_author(self, obj):
        return obj.publication.author.username

    @admin.display(description="Motif")
    def reason_preview(self, obj):
        return obj.reason if len(obj.reason) <= 80 else obj.reason[:80] + "..."

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
