from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "email_verified",
        "identity_verified",
        "identity_requested",
        "is_active",
        "is_staff",
        "failed_login_attempts",
        "locked_until",
        "date_joined",
    )

    list_filter = (
        "email_verified",
        "identity_verified",
        "identity_requested",
        "accept_cgu",
        "account_deactivated_by_user",
        "require_password_reset",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    ordering = (
        "-date_joined",
    )

    readonly_fields = (
        "last_login",
        "date_joined",
        "email_verification_code",
        "email_verification_code_expires",
        "password_reset_code",
        "password_reset_code_expires",
        "last_failed_login",
    )

    fieldsets = (
        (
            "👤 Informations du compte",
            {
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password",
                    "accept_cgu",
                ),
            },
        ),
        (
            "✉️ Vérification de l'adresse email",
            {
                "fields": (
                    "email_verified",
                    "email_verification_code",
                    "email_verification_code_expires",
                ),
            },
        ),
        (
            "🪪 Vérification d'identité",
            {
                "fields": (
                    "identity_verified",
                    "identity_requested",
                ),
            },
        ),
        (
            "🔐 Sécurité du compte",
            {
                "fields": (
                    "account_deactivated_by_user",
                    "require_password_reset",
                    "failed_login_attempts",
                    "last_failed_login",
                    "locked_until",
                ),
            },
        ),
        (
            "🔑 Réinitialisation du mot de passe",
            {
                "fields": (
                    "password_reset_code",
                    "password_reset_code_expires",
                ),
            },
        ),
        (
            "🛡️ Permissions Django",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "📅 Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            "Créer une utilisatrice",
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Vérification",
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    "accept_cgu",
                    "email_verified",
                    "identity_verified",
                    "identity_requested",
                ),
            },
        ),
        (
            "Statut du compte",
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
