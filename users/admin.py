from django.contrib import admin

from .models import UserBlock, UserProfile, UserReport


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


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "blocker",
        "blocked",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "blocker__username",
        "blocker__email",
        "blocker__first_name",
        "blocker__last_name",
        "blocked__username",
        "blocked__email",
        "blocked__first_name",
        "blocked__last_name",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "blocker",
        "blocked",
        "created_at",
    )

    fields = (
        "blocker",
        "blocked",
        "created_at",
    )

    list_select_related = (
        "blocker",
        "blocked",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reported_user",
        "reported_by",
        "reason_preview",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "reported__username",
        "reported__email",
        "reported__first_name",
        "reported__last_name",
        "reporter__username",
        "reporter__email",
        "reporter__first_name",
        "reporter__last_name",
        "reason",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "reporter",
        "reported",
        "reason",
        "created_at",
    )

    fields = (
        "reported",
        "reporter",
        "reason",
        "created_at",
    )

    list_select_related = (
        "reporter",
        "reported",
    )

    def reported_user(self, obj):
        return obj.reported.username

    reported_user.short_description = "Utilisateur signalé"
    reported_user.admin_order_field = "reported__username"

    def reported_by(self, obj):
        return obj.reporter.username

    reported_by.short_description = "Signalé par"
    reported_by.admin_order_field = "reporter__username"

    def reason_preview(self, obj):
        if not obj.reason:
            return "-"

        if len(obj.reason) <= 80:
            return obj.reason

        return obj.reason[:80] + "..."

    reason_preview.short_description = "Motif"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False