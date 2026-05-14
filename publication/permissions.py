from rest_framework.permissions import BasePermission


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
