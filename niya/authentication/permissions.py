# authentication/permissions.py
from rest_framework import permissions


class IsActiveOrPendingVerification(permissions.BasePermission):
    """
    Permet l'accès si l'utilisateur est authentifié ET (actif OU en attente de vérification).
    Contourne le blocage par défaut de Django sur is_active=False.
    """

    def has_permission(self, request, view):
        # 1. Vérifier que l'utilisateur est bien connecté (a un token valide)
        # On utilise la propriété is_authenticated qui est True si le token JWT est valide,
        # peu importe la valeur de is_active.
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user

        # 2. Logique métier personnalisée :
        # On autorise si le compte est actif...
        if user.is_active:
            return True

        # ... OU si le compte est inactif mais que l'email n'est pas encore vérifié
        # (C'est le cas juste après l'inscription)
        if not user.email_verified:
            return True

        # Dans tous les autres cas (ex: compte désactivé par admin, ou banni), on refuse
        return False