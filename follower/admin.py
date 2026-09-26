from django.contrib import admin

from .models import Follow, Friendship


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "follower",
        "followed",
        "created_at",
    )
    list_filter = (
        "created_at",
    )
    search_fields = (
        "follower__username",
        "followed__username",
        "follower__email",
        "followed__email",
    )
    readonly_fields = (
        "created_at",
    )
    ordering = (
        "-created_at",
    )


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "requester",
        "recipient",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "requester__username",
        "recipient__username",
        "requester__email",
        "recipient__email",
    )
    readonly_fields = (
        "created_at",
    )
    ordering = (
        "-created_at",
    )