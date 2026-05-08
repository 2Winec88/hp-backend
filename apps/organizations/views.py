from django.db.models import F
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Category,
    Event,
    EventImage,
    Organization,
    OrganizationBranch,
    OrganizationBranchImage,
    OrganizationMember,
    OrganizationNews,
    OrganizationNewsComment,
    OrganizationNewsImage,
    OrganizationRegistrationRequest,
)
from .permissions import (
    IsOrganizationManager,
    IsReadOnlyOrBranchImageOrganizationManager,
    IsReadOnlyOrBranchOrganizationManager,
    IsReadOnlyOrCommentAuthorOrOrganizationManager,
    IsReadOnlyOrEventImageAuthorOrOrganizationManager,
    IsReadOnlyOrOrganizationManager,
    IsReadOnlyOrOrganizationContentAuthorOrManager,
    IsReadOnlyOrOrganizationNewsImageAuthorOrOrganizationManager,
    IsStaffSuperuser,
)
from .serializers import (
    CategorySerializer,
    EventImageSerializer,
    EventSerializer,
    OrganizationBranchImageSerializer,
    OrganizationBranchSerializer,
    OrganizationSerializer,
    OrganizationNewsCommentSerializer,
    OrganizationNewsImageSerializer,
    OrganizationNewsSerializer,
    OrganizationMemberSerializer,
    OrganizationRegistrationDecisionSerializer,
    OrganizationRegistrationRequestCreateSerializer,
    OrganizationRegistrationRequestReadSerializer,
)
from .services import (
    approve_organization_registration_request,
    reject_organization_registration_request,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.select_related("created_by")
    serializer_class = OrganizationSerializer
    permission_classes = [IsReadOnlyOrOrganizationManager]
    http_method_names = ["get", "patch", "head", "options"]


class OrganizationMemberViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsOrganizationManager]
    http_method_names = ["get", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = OrganizationMember.objects.select_related(
            "organization",
            "user",
        )
        if not user or not user.is_authenticated:
            return queryset.none()

        managed_organization_ids = OrganizationMember.objects.filter(
            user=user,
            role=OrganizationMember.Role.MANAGER,
            is_active=True,
        ).values("organization_id")
        queryset = queryset.filter(
            organization_id__in=managed_organization_ids,
            is_active=True,
        )

        organization_id = self.request.query_params.get("organization")
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset

    def destroy(self, request, *args, **kwargs):
        membership = self.get_object()

        if membership.user_id == request.user.id:
            return Response(
                {"detail": "Managers cannot remove themselves from an organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if membership.role == OrganizationMember.Role.MANAGER:
            manager_count = OrganizationMember.objects.filter(
                organization=membership.organization,
                role=OrganizationMember.Role.MANAGER,
                is_active=True,
            ).count()
            if manager_count <= 1:
                return Response(
                    {"detail": "Cannot remove the last organization manager."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        membership.is_active = False
        membership.removed_at = timezone.now()
        membership.removed_by = request.user
        membership.save(update_fields=("is_active", "removed_at", "removed_by"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationBranchViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationBranchSerializer
    permission_classes = [IsReadOnlyOrBranchOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = OrganizationBranch.objects.select_related(
            "organization",
            "geodata",
            "geodata__city",
            "geodata__city__region",
        ).prefetch_related("images")
        organization_id = self.request.query_params.get("organization")
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        return queryset


class OrganizationBranchImageViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationBranchImageSerializer
    permission_classes = [IsReadOnlyOrBranchImageOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = OrganizationBranchImage.objects.select_related(
            "branch",
            "branch__organization",
        )
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        return queryset


class OrganizationContentViewSetMixin:
    def perform_create(self, serializer):
        organization = serializer.validated_data["organization"]
        member = OrganizationMember.objects.get(
            organization=organization,
            user=self.request.user,
            is_active=True,
        )
        serializer.save(created_by_member=member)


class EventViewSet(OrganizationContentViewSetMixin, viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsReadOnlyOrOrganizationContentAuthorOrManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Event.objects.select_related(
            "category",
            "created_by_member",
            "created_by_member__user",
            "organization",
        )


class EventImageViewSet(viewsets.ModelViewSet):
    serializer_class = EventImageSerializer
    permission_classes = [IsReadOnlyOrEventImageAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = EventImage.objects.select_related(
            "event",
            "event__organization",
            "event__created_by_member",
            "event__created_by_member__user",
        )
        event_id = self.request.query_params.get("event")
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset


class OrganizationNewsViewSet(OrganizationContentViewSetMixin, viewsets.ModelViewSet):
    serializer_class = OrganizationNewsSerializer
    permission_classes = [IsReadOnlyOrOrganizationContentAuthorOrManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = OrganizationNews.objects.select_related(
            "created_by_member",
            "created_by_member__user",
            "organization",
        ).prefetch_related("images")
        organization_id = self.request.query_params.get("organization")
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        OrganizationNews.objects.filter(pk=instance.pk).update(
            views_count=F("views_count") + 1
        )
        instance.refresh_from_db(fields=("views_count",))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


EventNewsViewSet = OrganizationNewsViewSet


class OrganizationNewsImageViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationNewsImageSerializer
    permission_classes = [IsReadOnlyOrOrganizationNewsImageAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = OrganizationNewsImage.objects.select_related(
            "news",
            "news__organization",
            "news__created_by_member",
            "news__created_by_member__user",
        )
        news_id = self.request.query_params.get("news")
        if news_id:
            queryset = queryset.filter(news_id=news_id)
        return queryset


class OrganizationNewsCommentViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationNewsCommentSerializer
    permission_classes = [IsReadOnlyOrCommentAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = OrganizationNewsComment.objects.select_related(
            "created_by",
            "news",
            "news__organization",
        )
        news_id = self.request.query_params.get("news")
        if news_id:
            queryset = queryset.filter(news_id=news_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


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
