# identity_verification/admin.py
from django.contrib import admin
from .models import IdentityVerificationRequest


@admin.register(IdentityVerificationRequest)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['user', 'id_card_front', 'selfie_with_id', 'ai_score', 'ai_details', 'created_at']

    fieldsets = (
        ('Utilisatrice', {'fields': ('user', 'created_at')}),
        ('Documents', {'fields': ('id_card_front', 'selfie_with_id')}),
        ('Analyse Automatique (Futur)', {'fields': ('ai_score', 'ai_details'), 'classes': ('collapse',)}),
        ('Décision Admin', {'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at')}),
    )

    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        for req in queryset:
            if req.status == 'PENDING':
                req.approve(request.user)
        self.message_user(request, f"{queryset.count()} demandes approuvées avec succès.")

    def reject_selected(self, request, queryset):
        # Pour le rejet en masse, on met une raison générique car on ne peut pas demander input par ligne facilement dans l'action
        for req in queryset:
            if req.status == 'PENDING':
                req.reject(request.user, "Rejeté via action en masse admin.")
        self.message_user(request, f"{queryset.count()} demandes rejetées.")