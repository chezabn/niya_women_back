from django.conf import settings
from django.db import models
from django.utils import timezone


class IdentityVerificationRequest(models.Model):
    """
    Stocke la demande de vérification d'identité d'une utilisatrice.
    Une utilisatrice ne peut avoir qu'une demande active à la fois.
    """

    STATUS_CHOICES = [
        ("PENDING", "En attente de revue"),
        ("APPROVED", "Validé (Identité confirmée)"),
        ("REJECTED", "Rejeté"),
        ("ERROR", "Erreur de traitement"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="identity_request",
        unique=True,
    )

    # Photos fournies
    id_card_front = models.ImageField(upload_to="verifications/id_cards/%Y/%m/%d/")
    selfie_with_id = models.ImageField(upload_to="verifications/selfies/%Y/%m/%d/")

    # Champs pour évolution future (IA / API Externe)
    # On les garde nullable pour l'instant (validation manuelle pure)
    ai_score = models.FloatField(
        null=True, blank=True, help_text="Score de confiance IA (0-1)"
    )
    ai_details = models.JSONField(
        null=True, blank=True, help_text="Détails bruts de l'analyse IA/API"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    # Champs de suivi Admin
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_verifications",
        limit_choices_to={"is_staff": True},  # Seul le staff peut reviewer
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(
        blank=True, help_text="Raison du rejet (visible par l'admin)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Vérification pour {self.user.username} - {self.status}"

    def approve(self, admin_user):
        """Méthode utilitaire pour approuver"""
        self.status = "APPROVED"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()

        # ACTION CRITIQUE : Activer le compte utilisateur
        self.user.is_active = True
        self.user.identity_verified = True
        self.user.email_verified = (
            True  # On considère que l'identité valide l'email aussi
        )
        self.user.save()

    def reject(self, admin_user, reason=""):
        """Méthode utilitaire pour rejeter"""
        self.status = "REJECTED"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()
