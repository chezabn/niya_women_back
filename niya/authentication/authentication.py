# authentication/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CustomJWTAuthentication(JWTAuthentication):
    """
    Classe d'authentification JWT personnalisée qui ignore le statut is_active.
    Cela permet aux utilisateurs non actifs (en attente de vérification)
    de recevoir un token valide.
    """

    def get_user(self, validated_token):
        """
        Récupère l'utilisateur associé au token.
        On surcharge cette méthode pour NE PAS vérifier is_active ici.
        La vérification sera faite plus tard par nos Permissions (IsActiveOrPendingVerification).
        """
        from .models import User  # Import local pour éviter les cycles

        try:
            user_id = validated_token['user_id']
        except KeyError:
            raise AuthenticationFailed('Token ne contient pas d\'ID utilisateur', code='no_user_id')

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('Utilisateur non trouvé', code='user_not_found')

        # IMPORTANT : On retire la vérification "if not user.is_active"
        # qui est présente dans la classe parente.
        # On retourne l'utilisateur quoi qu'il arrive (actif ou non).
        return user