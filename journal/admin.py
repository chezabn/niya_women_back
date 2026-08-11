from django.contrib import admin

from .models import Journal


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "title",
        "page_preview",
        "date",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "date",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "page",
        "author__username",
        "author__email",
        "author__first_name",
        "author__last_name",
    )

    ordering = (
        "-date",
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fields = (
        "author",
        "title",
        "page",
        "date",
        "created_at",
        "updated_at",
    )

    def page_preview(self, obj):
        if len(obj.page) <= 80:
            return obj.page
        return obj.page[:80] + "..."

    page_preview.short_description = "Page"