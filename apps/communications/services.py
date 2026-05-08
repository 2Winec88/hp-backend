from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .invitation_handlers import invitation_handlers
from .models import Invitation, Notification
from .tasks import send_notification_delivery, send_notification_push_delivery


def create_notification(
    *,
    recipient,
    actor=None,
    type=Notification.Type.TEXT,
    title,
    body="",
    payload=None,
    send_email=False,
    send_push=False,
):
    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        type=type,
        title=title,
        body=body,
        payload=payload or {},
    )

    if send_email:
        transaction.on_commit(
            lambda: send_notification_delivery.delay(notification.pk)
        )
    if send_push:
        transaction.on_commit(
            lambda: send_notification_push_delivery.delay(notification.pk)
        )

    return notification


@transaction.atomic
def create_invitation(
    *,
    target_type,
    target_id,
    invited_user,
    invited_by,
    role,
    send_email=True,
    send_push=True,
    expires_at=None,
):
    handler = invitation_handlers.get_by_target_type(target_type)
    target = invitation_handlers.get_target(target_type=target_type, target_id=target_id)

    if role not in handler.allowed_roles:
        raise ValidationError({"role": "Unsupported role for this invitation target."})

    if invited_user == invited_by:
        raise ValidationError({"invited_user": "You cannot invite yourself."})

    if not handler.can_invite(inviter=invited_by, target=target):
        raise PermissionDenied("You do not have permission to invite users to this target.")

    if handler.is_member(user=invited_user, target=target):
        raise ValidationError({"invited_user": "User is already a member of this target."})

    content_type = invitation_handlers.get_content_type(target_type=target_type)
    notification = create_notification(
        recipient=invited_user,
        actor=invited_by,
        type=Notification.Type.INVITATION,
        title=handler.get_notification_title(target=target, role=role),
        body=handler.get_notification_body(inviter=invited_by, target=target, role=role),
        payload={
            "target_type": target_type,
            "target_id": target.pk,
            "role": role,
        },
        send_email=send_email,
        send_push=send_push,
    )

    try:
        invitation = Invitation.objects.create(
            content_type=content_type,
            object_id=target.pk,
            invited_user=invited_user,
            invited_by=invited_by,
            role=role,
            notification=notification,
            expires_at=expires_at or Invitation.default_expires_at(),
        )
    except IntegrityError as exc:
        raise ValidationError("A pending invitation already exists for this user.") from exc

    notification.payload = {
        **notification.payload,
        "invitation_id": invitation.pk,
    }
    notification.save(update_fields=("payload",))
    return invitation


@transaction.atomic
def accept_invitation(*, invitation, user):
    invitation = Invitation.objects.select_for_update().get(pk=invitation.pk)

    if invitation.invited_user_id != user.id:
        raise PermissionDenied("Only the invited user can accept this invitation.")

    if invitation.status != Invitation.Status.PENDING:
        raise ValidationError("Only pending invitations can be accepted.")

    if invitation.is_expired:
        invitation.status = Invitation.Status.EXPIRED
        invitation.save(update_fields=("status", "updated_at"))
        raise ValidationError("This invitation has expired.")

    handler = invitation_handlers.get_by_content_type(invitation.content_type)
    handler.create_membership(
        user=user,
        target=invitation.target,
        role=invitation.role,
    )

    invitation.status = Invitation.Status.ACCEPTED
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=("status", "accepted_at", "updated_at"))

    if invitation.notification:
        invitation.notification.mark_read()

    return invitation


@transaction.atomic
def decline_invitation(*, invitation, user):
    invitation = Invitation.objects.select_for_update().get(pk=invitation.pk)

    if invitation.invited_user_id != user.id:
        raise PermissionDenied("Only the invited user can decline this invitation.")

    if invitation.status != Invitation.Status.PENDING:
        raise ValidationError("Only pending invitations can be declined.")

    invitation.status = Invitation.Status.DECLINED
    invitation.declined_at = timezone.now()
    invitation.save(update_fields=("status", "declined_at", "updated_at"))

    if invitation.notification:
        invitation.notification.mark_read()

    return invitation


@transaction.atomic
def cancel_invitation(*, invitation, user):
    invitation = Invitation.objects.select_for_update().get(pk=invitation.pk)
    handler = invitation_handlers.get_by_content_type(invitation.content_type)

    if not handler.can_invite(inviter=user, target=invitation.target):
        raise PermissionDenied("You do not have permission to cancel this invitation.")

    if invitation.status != Invitation.Status.PENDING:
        raise ValidationError("Only pending invitations can be cancelled.")

    invitation.status = Invitation.Status.CANCELLED
    invitation.cancelled_at = timezone.now()
    invitation.save(update_fields=("status", "cancelled_at", "updated_at"))
    return invitation
