from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError

from apps.organizations.models import Organization, OrganizationMember


class OrganizationInvitationHandler:
    target_type = "organization"
    model = Organization
    allowed_roles = {
        OrganizationMember.Role.MANAGER,
        OrganizationMember.Role.MEMBER,
    }

    def can_invite(self, *, inviter, target):
        return OrganizationMember.objects.filter(
            organization=target,
            user=inviter,
            role=OrganizationMember.Role.MANAGER,
            is_active=True,
        ).exists()

    def is_member(self, *, user, target):
        return OrganizationMember.objects.filter(
            organization=target,
            user=user,
            is_active=True,
        ).exists()

    def create_membership(self, *, user, target, role):
        membership, created = OrganizationMember.objects.get_or_create(
            organization=target,
            user=user,
            defaults={"role": role},
        )
        if not created and not membership.is_active:
            membership.role = role
            membership.is_active = True
            membership.removed_at = None
            membership.removed_by = None
            membership.save(
                update_fields=(
                    "role",
                    "is_active",
                    "removed_at",
                    "removed_by",
                )
            )
        return membership, created

    def get_notification_title(self, *, target, role):
        return f"Invitation to {target.official_name}"

    def get_notification_body(self, *, inviter, target, role):
        return (
            f"{inviter.get_full_name() or inviter.email} invited you to join "
            f"{target.official_name} as {role}."
        )


class InvitationHandlerRegistry:
    def __init__(self):
        self._handlers = {}

    def register(self, handler):
        self._handlers[handler.target_type] = handler

    def get_by_target_type(self, target_type):
        try:
            return self._handlers[target_type]
        except KeyError as exc:
            raise ValidationError({"target_type": "Unsupported invitation target type."}) from exc

    def get_by_content_type(self, content_type):
        for handler in self._handlers.values():
            if content_type.model_class() == handler.model:
                return handler
        raise ValidationError("Unsupported invitation target type.")

    def get_target(self, *, target_type, target_id):
        handler = self.get_by_target_type(target_type)
        try:
            return handler.model.objects.get(pk=target_id)
        except handler.model.DoesNotExist as exc:
            raise ValidationError({"target_id": "Invitation target was not found."}) from exc

    def get_content_type(self, *, target_type):
        handler = self.get_by_target_type(target_type)
        return ContentType.objects.get_for_model(handler.model)

    def get_target_type(self, *, content_type):
        return self.get_by_content_type(content_type).target_type


invitation_handlers = InvitationHandlerRegistry()
invitation_handlers.register(OrganizationInvitationHandler())
