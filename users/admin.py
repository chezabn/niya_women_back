from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "bio_preview",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "bio",
    )

    ordering = (
        "user__username",
    )

    fields = (
        "user",
        "bio",
    )

    readonly_fields = (
        "user",
    )

    def bio_preview(self, obj):
        if not obj.bio:
            return "-"

        if len(obj.bio) <= 60:
            return obj.bio

        return obj.bio[:60] + "..."

    bio_preview.short_description = "Bio"