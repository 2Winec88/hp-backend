from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.collections.permissions import (
    is_donor_group_collection_author_or_manager,
    is_donor_group_member,
)
from apps.organizations.models import OrganizationMember
from apps.organizations.permissions import is_active_organization_manager

from .invitation_handlers import invitation_handlers
from .models import (
    DonorGroupMessage,
    Invitation,
    Notification,
    NotificationDelivery,
    OrganizationMessage,
    UserDevice,
)
from .services import create_invitation, create_notification


User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)
    recipient_email = serializers.EmailField(source="recipient.email", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "recipient",
            "recipient_email",
            "actor",
            "actor_email",
            "type",
            "title",
            "body",
            "payload",
            "is_read",
            "read_at",
            "email_sent_at",
            "created_at",
        )
        read_only_fields = (
            "id",
            "actor",
            "actor_email",
            "recipient_email",
            "is_read",
            "read_at",
            "email_sent_at",
            "created_at",
        )


class UserDeviceSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserDevice
        fields = (
            "id",
            "user",
            "user_email",
            "provider",
            "token",
            "device_id",
            "platform",
            "app_version",
            "is_active",
            "last_seen_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "user_email",
            "last_seen_at",
            "created_at",
            "updated_at",
        )


class NotificationDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDelivery
        fields = (
            "id",
            "notification",
            "channel",
            "status",
            "device",
            "error",
            "sent_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrganizationMessageSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)
    author_full_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = OrganizationMessage
        fields = (
            "id",
            "organization",
            "author",
            "author_email",
            "author_full_name",
            "text",
            "deleted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "author_email",
            "author_full_name",
            "deleted_at",
            "created_at",
            "updated_at",
        )

    def validate_organization(self, organization):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not _is_active_organization_member(organization=organization, user=user):
            raise serializers.ValidationError("Only organization members can write to this chat.")
        return organization

    def validate(self, attrs):
        if self.instance and "organization" in attrs and attrs["organization"] != self.instance.organization:
            raise serializers.ValidationError({"organization": "Organization cannot be changed."})
        text = attrs.get("text", getattr(self.instance, "text", ""))
        if not text.strip():
            raise serializers.ValidationError({"text": "Message text cannot be blank."})
        return attrs


class DonorGroupMessageSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)
    author_full_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = DonorGroupMessage
        fields = (
            "id",
            "donor_group",
            "author",
            "author_email",
            "author_full_name",
            "text",
            "deleted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "author_email",
            "author_full_name",
            "deleted_at",
            "created_at",
            "updated_at",
        )

    def validate_donor_group(self, donor_group):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_donor_group_member(donor_group=donor_group, user=user):
            raise serializers.ValidationError("Only donor group members can write to this chat.")
        if donor_group.is_delivery_completed:
            raise serializers.ValidationError("Completed donor group chat is archived.")
        return donor_group

    def validate(self, attrs):
        if self.instance and "donor_group" in attrs and attrs["donor_group"] != self.instance.donor_group:
            raise serializers.ValidationError({"donor_group": "Donor group cannot be changed."})
        donor_group = attrs.get("donor_group", getattr(self.instance, "donor_group", None))
        if donor_group and donor_group.is_delivery_completed:
            raise serializers.ValidationError("Completed donor group chat is archived.")
        text = attrs.get("text", getattr(self.instance, "text", ""))
        if not text.strip():
            raise serializers.ValidationError({"text": "Message text cannot be blank."})
        return attrs


class NotificationCreateSerializer(serializers.Serializer):
    recipient = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    type = serializers.ChoiceField(
        choices=(
            Notification.Type.TEXT,
            Notification.Type.MESSAGE,
            Notification.Type.SYSTEM,
        ),
        default=Notification.Type.TEXT,
    )
    title = serializers.CharField(max_length=255)
    body = serializers.CharField(required=False, allow_blank=True)
    payload = serializers.JSONField(required=False)
    send_email = serializers.BooleanField(default=False)
    send_push = serializers.BooleanField(default=False)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        if (attrs.get("send_email") or attrs.get("send_push")) and not (
            user.is_staff and user.is_superuser
        ):
            raise serializers.ValidationError(
                "Only staff superusers can request external notification delivery."
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return create_notification(
            recipient=validated_data["recipient"],
            actor=request.user,
            type=validated_data["type"],
            title=validated_data["title"],
            body=validated_data.get("body", ""),
            payload=validated_data.get("payload") or {},
            send_email=validated_data["send_email"],
            send_push=validated_data["send_push"],
        )


class InvitationSerializer(serializers.ModelSerializer):
    invited_user_email = serializers.EmailField(source="invited_user.email", read_only=True)
    invited_by_email = serializers.EmailField(source="invited_by.email", read_only=True)
    target_type = serializers.SerializerMethodField()
    target_id = serializers.IntegerField(source="object_id", read_only=True)

    class Meta:
        model = Invitation
        fields = (
            "id",
            "target_type",
            "target_id",
            "invited_user",
            "invited_user_email",
            "invited_by",
            "invited_by_email",
            "role",
            "status",
            "notification",
            "expires_at",
            "accepted_at",
            "declined_at",
            "cancelled_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_target_type(self, obj):
        return invitation_handlers.get_target_type(content_type=obj.content_type)


class InvitationCreateSerializer(serializers.Serializer):
    target_type = serializers.CharField()
    target_id = serializers.IntegerField(min_value=1)
    invited_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = serializers.CharField(default="member", max_length=30)
    send_email = serializers.BooleanField(default=True)
    send_push = serializers.BooleanField(default=True)
    expires_at = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        request = self.context["request"]
        return create_invitation(
            target_type=validated_data["target_type"],
            target_id=validated_data["target_id"],
            invited_user=validated_data["invited_user"],
            invited_by=request.user,
            role=validated_data["role"],
            send_email=validated_data["send_email"],
            send_push=validated_data["send_push"],
            expires_at=validated_data.get("expires_at"),
        )


def _is_active_organization_member(*, organization, user):
    if not user or not user.is_authenticated:
        return False
    return OrganizationMember.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
    ).exists()


def can_manage_organization_message(*, message, user):
    if not user or not user.is_authenticated:
        return False
    if message.author_id == user.id:
        return True
    return is_active_organization_manager(
        organization=message.organization,
        user=user,
    )


def can_manage_donor_group_message(*, message, user):
    if not user or not user.is_authenticated:
        return False
    if message.author_id == user.id:
        return True
    return is_donor_group_collection_author_or_manager(
        donor_group=message.donor_group,
        user=user,
    )
