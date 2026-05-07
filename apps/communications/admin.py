from django.contrib import admin

from .models import Invitation, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "actor", "type", "title", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at", "email_sent_at")
    search_fields = ("recipient__email", "actor__email", "title", "body")
    autocomplete_fields = ("recipient", "actor")
    readonly_fields = ("created_at", "read_at", "email_sent_at")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "target",
        "invited_user",
        "invited_by",
        "role",
        "status",
        "expires_at",
        "created_at",
    )
    list_filter = ("status", "role", "content_type", "created_at", "expires_at")
    search_fields = ("invited_user__email", "invited_by__email", "role")
    autocomplete_fields = ("invited_user", "invited_by", "notification")
    readonly_fields = ("created_at", "updated_at", "accepted_at", "declined_at", "cancelled_at")
