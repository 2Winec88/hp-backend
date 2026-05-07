from django.contrib.auth import get_user_model
from rest_framework import serializers

from .invitation_handlers import invitation_handlers
from .models import Invitation, Notification
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
            expires_at=validated_data.get("expires_at"),
        )
