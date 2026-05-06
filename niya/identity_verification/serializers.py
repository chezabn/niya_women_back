# identity_verification/serializers.py
from rest_framework import serializers
from .models import IdentityVerificationRequest

class VerificationRequestSerializer(serializers.ModelSerializer):
    """Pour l'utilisatrice qui soumet sa demande"""
    class Meta:
        model = IdentityVerificationRequest
        fields = ['id_card_front', 'selfie_with_id']
        # On ne expose pas le status ou les champs admin ici

class AdminVerificationReviewSerializer(serializers.Serializer):
    """Pour l'admin qui valide ou rejette"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError("Une raison est obligatoire pour un rejet.")
        return data