from rest_framework.permissions import BasePermission
from .utils import user_has_role
from .constants import ROLE_SYSTEM_ADMIN


class RoleRequiredPermission(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        required_roles = getattr(view, "required_roles", None)
        if required_roles is None:
            return True
        if request.user and request.user.is_superuser:
            return True
        if user_has_role(request.user, [ROLE_SYSTEM_ADMIN]):
            return True
        return user_has_role(request.user, required_roles)
