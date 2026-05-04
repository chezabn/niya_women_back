# authentication/permissions.py
from rest_framework import permissions


class IsActiveOrPendingVerification(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user

        if user.is_active:
            return True
        if not user.email_verified:
            return True

        return False