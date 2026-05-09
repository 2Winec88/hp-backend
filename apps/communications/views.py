from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import DonorGroupMessage, Invitation, Notification
from .models import NotificationDelivery, OrganizationMessage, UserDevice
from .serializers import (
    DonorGroupMessageSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    NotificationCreateSerializer,
    NotificationDeliverySerializer,
    NotificationSerializer,
    OrganizationMessageSerializer,
    UserDeviceSerializer,
    can_manage_donor_group_message,
    can_manage_organization_message,
)
from .services import accept_invitation, cancel_invitation, decline_invitation


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = Notification.objects.select_related("recipient", "actor").filter(
            recipient=self.request.user,
        )
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == "true")
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return NotificationCreateSerializer
        return NotificationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        response_serializer = NotificationSerializer(
            notification,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = 0
        for notification in self.get_queryset().filter(is_read=False):
            notification.mark_read()
            updated += 1
        return Response({"updated": updated}, status=status.HTTP_200_OK)


class UserDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = UserDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return UserDevice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationDeliverySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = NotificationDelivery.objects.select_related(
            "notification",
            "device",
        ).filter(notification__recipient=self.request.user)
        notification_id = self.request.query_params.get("notification")
        if notification_id:
            queryset = queryset.filter(notification_id=notification_id)
        channel = self.request.query_params.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)
        return queryset


class OrganizationMessageViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = OrganizationMessage.objects.select_related(
            "organization",
            "author",
        ).filter(
            organization__members__user=self.request.user,
            organization__members__is_active=True,
        ).distinct()
        organization_id = self.request.query_params.get("organization")
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        after_id = self.request.query_params.get("after_id")
        if after_id:
            queryset = queryset.filter(id__gt=after_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if not can_manage_organization_message(
            message=self.get_object(),
            user=self.request.user,
        ):
            raise PermissionDenied("Only the message author or organization manager can edit this message.")
        serializer.save()

    def perform_destroy(self, instance):
        if not can_manage_organization_message(
            message=instance,
            user=self.request.user,
        ):
            raise PermissionDenied("Only the message author or organization manager can delete this message.")
        instance.deleted_at = timezone.now()
        instance.save(update_fields=("deleted_at", "updated_at"))


class DonorGroupMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DonorGroupMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = DonorGroupMessage.objects.select_related(
            "donor_group",
            "donor_group__collection",
            "donor_group__collection__organization",
            "donor_group__collection__created_by_member",
            "donor_group__collection__created_by_member__user",
            "author",
        ).filter(
            Q(donor_group__members__user=self.request.user)
            | Q(
                donor_group__collection__created_by_member__user=self.request.user,
                donor_group__collection__created_by_member__is_active=True,
            )
            | Q(
                donor_group__collection__organization__members__user=self.request.user,
                donor_group__collection__organization__members__is_active=True,
                donor_group__collection__organization__members__role="manager",
            )
        ).distinct()
        donor_group_id = self.request.query_params.get("donor_group")
        if donor_group_id:
            queryset = queryset.filter(donor_group_id=donor_group_id)
        after_id = self.request.query_params.get("after_id")
        if after_id:
            queryset = queryset.filter(id__gt=after_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if not can_manage_donor_group_message(
            message=self.get_object(),
            user=self.request.user,
        ):
            raise PermissionDenied("Only the message author or donor group manager can edit this message.")
        serializer.save()

    def perform_destroy(self, instance):
        if not can_manage_donor_group_message(
            message=instance,
            user=self.request.user,
        ):
            raise PermissionDenied("Only the message author or donor group manager can delete this message.")
        instance.deleted_at = timezone.now()
        instance.save(update_fields=("deleted_at", "updated_at"))


class InvitationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return Invitation.objects.select_related(
            "content_type",
            "invited_user",
            "invited_by",
            "notification",
        ).filter(
            Q(invited_user=self.request.user) | Q(invited_by=self.request.user)
        )

    def get_serializer_class(self):
        if self.action == "create":
            return InvitationCreateSerializer
        return InvitationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        response_serializer = InvitationSerializer(
            invitation,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        invitation = accept_invitation(invitation=self.get_object(), user=request.user)
        serializer = self.get_serializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        invitation = decline_invitation(invitation=self.get_object(), user=request.user)
        serializer = self.get_serializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        invitation = cancel_invitation(invitation=self.get_object(), user=request.user)
        serializer = self.get_serializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)
