from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import OrganizationMember


def is_active_organization_manager(*, organization, user):
    return organization.members.filter(
        user=user,
        role=OrganizationMember.Role.MANAGER,
        is_active=True,
    ).exists()


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


class IsReadOnlyOrOrganizationContentAuthorOrManager(BasePermission):
    message = "Only the author or an organization manager can edit this organization content."

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
        if obj.created_by_member.user_id == user.id and obj.created_by_member.is_active:
            return True
        return is_active_organization_manager(organization=obj.organization, user=user)


IsReadOnlyOrEventNewsAuthorOrOrganizationManager = IsReadOnlyOrOrganizationContentAuthorOrManager
IsReadOnlyOrEventAuthorOrOrganizationManager = IsReadOnlyOrOrganizationContentAuthorOrManager


class IsReadOnlyOrCommentAuthorOrOrganizationManager(BasePermission):
    message = "Only the comment author or an organization manager can edit this comment."

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
        if obj.created_by_id == user.id:
            return True
        return is_active_organization_manager(organization=obj.news.organization, user=user)


class IsOrganizationManager(BasePermission):
    message = "Only an organization manager can manage organization members."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return is_active_organization_manager(organization=obj.organization, user=user)


class IsReadOnlyOrOrganizationManager(BasePermission):
    message = "Only an active organization manager can edit this organization."

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
        return is_active_organization_manager(organization=obj, user=user)


class IsReadOnlyOrBranchOrganizationManager(BasePermission):
    message = "Only an active organization manager can edit this branch."

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
        return is_active_organization_manager(organization=obj.organization, user=user)


class IsReadOnlyOrBranchImageOrganizationManager(BasePermission):
    message = "Only an active organization manager can edit this branch image."

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
        return is_active_organization_manager(
            organization=obj.branch.organization,
            user=user,
        )


class IsReadOnlyOrEventImageAuthorOrOrganizationManager(BasePermission):
    message = "Only the event author or an active organization manager can edit this event image."

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
        if obj.event.created_by_member.user_id == user.id and obj.event.created_by_member.is_active:
            return True
        return is_active_organization_manager(
            organization=obj.event.organization,
            user=user,
        )


class IsReadOnlyOrOrganizationNewsImageAuthorOrOrganizationManager(BasePermission):
    message = "Only the news author or an active organization manager can edit this news image."

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
        if obj.news.created_by_member.user_id == user.id and obj.news.created_by_member.is_active:
            return True
        return is_active_organization_manager(
            organization=obj.news.organization,
            user=user,
        )
