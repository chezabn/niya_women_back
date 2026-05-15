from rest_framework.permissions import BasePermission


class IsFullyAuthenticated(BasePermission):
    """
    Grants access only to fully verified users.
    """

    message = "Full authentication is required " "to access this resource."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not user.is_active:
            return False
        id_verification = getattr(
            user,
            "identity_verified",
            None,
        )
        if not id_verification:
            return False
        mail_verification = getattr(
            user,
            "email_verified",
            None,
        )
        if not mail_verification:
            return False
        return True


class IsPublicationOwner(BasePermission):
    """
    Allows access only to publication owners.
    """

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ) -> bool:
        return obj.author == request.user
