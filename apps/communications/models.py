from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Notification(models.Model):
    class Type(models.TextChoices):
        INVITATION = "invitation", "Invitation"
        MESSAGE = "message", "Message"
        SYSTEM = "system", "System"
        TEXT = "text", "Text"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.TEXT,
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"{self.recipient} - {self.title}"

    def mark_read(self):
        if self.is_read:
            return
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=("is_read", "read_at"))


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_invitations",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
    )
    role = models.CharField(max_length=30, default="member")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    notification = models.OneToOneField(
        Notification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitation",
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invitations"
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("content_type", "object_id", "invited_user"),
                condition=Q(status="pending"),
                name="unique_pending_invitation_per_target_user",
            ),
        ]

    def __str__(self):
        return f"{self.invited_user} -> {self.target} ({self.status})"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @classmethod
    def default_expires_at(cls):
        return timezone.now() + timedelta(days=7)
