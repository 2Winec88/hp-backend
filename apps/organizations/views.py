from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Event, EventNews, OrganizationMember, OrganizationRegistrationRequest
from .permissions import (
    IsReadOnlyOrEventAuthorOrOrganizationManager,
    IsReadOnlyOrEventNewsAuthorOrOrganizationManager,
    IsStaffSuperuser,
)
from .serializers import (
    EventSerializer,
    EventNewsSerializer,
    OrganizationRegistrationDecisionSerializer,
    OrganizationRegistrationRequestCreateSerializer,
    OrganizationRegistrationRequestReadSerializer,
)
from .services import (
    approve_organization_registration_request,
    reject_organization_registration_request,
)


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsReadOnlyOrEventAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Event.objects.select_related(
            "category",
            "created_by_member",
            "created_by_member__user",
            "organization",
        )

    def perform_create(self, serializer):
        organization = serializer.validated_data["organization"]
        member = OrganizationMember.objects.get(
            organization=organization,
            user=self.request.user,
        )
        serializer.save(created_by_member=member)


class EventNewsViewSet(viewsets.ModelViewSet):
    serializer_class = EventNewsSerializer
    permission_classes = [IsReadOnlyOrEventNewsAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = EventNews.objects.select_related(
            "created_by_member",
            "created_by_member__user",
            "event",
            "event__organization",
        )
        event_id = self.request.query_params.get("event")
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset

    def perform_create(self, serializer):
        event = serializer.validated_data["event"]
        member = OrganizationMember.objects.get(
            organization=event.organization,
            user=self.request.user,
        )
        serializer.save(created_by_member=member)


class OrganizationRegistrationRequestViewSet(viewsets.ModelViewSet):
    queryset = OrganizationRegistrationRequest.objects.select_related(
        "created_by",
        "reviewed_by",
        "organization",
    )
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()
        if user.is_staff and user.is_superuser:
            return queryset
        return queryset.filter(created_by=user)

    def get_permissions(self):
        if self.action in ("approve", "reject"):
            permission_classes = [permissions.IsAuthenticated, IsStaffSuperuser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return OrganizationRegistrationRequestCreateSerializer
        if self.action == "reject":
            return OrganizationRegistrationDecisionSerializer
        return OrganizationRegistrationRequestReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response_serializer = OrganizationRegistrationRequestReadSerializer(
            instance,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        registration_request = self.get_object()
        registration_request = approve_organization_registration_request(
            registration_request=registration_request,
            reviewer=request.user,
        )
        serializer = OrganizationRegistrationRequestReadSerializer(
            registration_request,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        registration_request = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registration_request = reject_organization_registration_request(
            registration_request=registration_request,
            reviewer=request.user,
            rejection_reason=serializer.validated_data["rejection_reason"],
        )
        response_serializer = OrganizationRegistrationRequestReadSerializer(
            registration_request,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)
