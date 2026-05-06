from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import OrganizationMember


class IsStaffSuperuser(BasePermission):
    message = "Staff superuser access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_staff
            and user.is_superuser
        )


class IsReadOnlyOrEventNewsAuthorOrOrganizationManager(BasePermission):
    message = "Only the news author or an organization manager can edit this event news."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False
        if obj.created_by_member.user_id == user.id:
            return True
        return obj.event.organization.members.filter(
            user=user,
            role=OrganizationMember.Role.MANAGER,
        ).exists()


class IsReadOnlyOrEventAuthorOrOrganizationManager(BasePermission):
    message = "Only the event author or an organization manager can edit this event."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False
        if obj.created_by_member.user_id == user.id:
            return True
        return obj.organization.members.filter(
            user=user,
            role=OrganizationMember.Role.MANAGER,
        ).exists()
