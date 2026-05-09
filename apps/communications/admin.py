from django.contrib import admin

from .models import (
    DonorGroupMessage,
    Invitation,
    Notification,
    NotificationDelivery,
    OrganizationMessage,
    UserDevice,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "actor", "type", "title", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at", "email_sent_at")
    search_fields = ("recipient__email", "actor__email", "title", "body")
    autocomplete_fields = ("recipient", "actor")
    readonly_fields = ("created_at", "read_at", "email_sent_at")


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "provider", "platform", "is_active", "updated_at")
    list_filter = ("provider", "platform", "is_active", "created_at")
    search_fields = ("user__email", "token", "device_id")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "last_seen_at")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "notification", "channel", "status", "device", "sent_at", "created_at")
    list_filter = ("channel", "status", "created_at", "sent_at")
    search_fields = ("notification__title", "notification__recipient__email", "error")
    autocomplete_fields = ("notification", "device")
    readonly_fields = ("created_at", "updated_at", "sent_at")


@admin.register(OrganizationMessage)
class OrganizationMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "author", "created_at", "deleted_at")
    list_filter = ("created_at", "deleted_at")
    search_fields = ("organization__official_name", "author__email", "text")
    autocomplete_fields = ("organization", "author")
    readonly_fields = ("created_at", "updated_at", "deleted_at")


@admin.register(DonorGroupMessage)
class DonorGroupMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "donor_group", "author", "created_at", "deleted_at")
    list_filter = ("created_at", "deleted_at")
    search_fields = ("donor_group__title", "author__email", "text")
    autocomplete_fields = ("donor_group", "author")
    readonly_fields = ("created_at", "updated_at", "deleted_at")


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
