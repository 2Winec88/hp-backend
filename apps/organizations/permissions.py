from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    message = "Moderator role is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.roles.filter(code="moderator").exists()
        )
