from rest_framework import serializers, viewsets

from apps.organizations.models import OrganizationMember

from .models import (
    BranchItem,
    Collection,
    CollectionItem,
    CourierProfile,
    DonorGroup,
    DonorGroupItem,
    DonorGroupMember,
    ItemCategory,
    UserItem,
)
from .permissions import (
    IsReadOnlyOrBranchItemOrganizationManager,
    IsReadOnlyOrCollectionAuthorOrOrganizationManager,
    IsReadOnlyOrCollectionItemAuthorOrOrganizationManager,
    IsReadOnlyOrCourierProfileOwner,
    IsReadOnlyOrDonorGroupCollectionAuthorOrOrganizationManager,
    IsReadOnlyOrDonorGroupItemManager,
    IsReadOnlyOrDonorGroupMemberManager,
    IsReadOnlyOrUserItemOwner,
)
from .serializers import (
    BranchItemSerializer,
    CollectionItemSerializer,
    CollectionSerializer,
    CourierProfileSerializer,
    DonorGroupItemSerializer,
    DonorGroupMemberSerializer,
    DonorGroupSerializer,
    ItemCategorySerializer,
    UserItemSerializer,
)


class ItemCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        queryset = ItemCategory.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ("1", "true", "yes"))
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class UserItemViewSet(viewsets.ModelViewSet):
    serializer_class = UserItemSerializer
    permission_classes = [IsReadOnlyOrUserItemOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = UserItem.objects.select_related("user", "category")
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(category__name__icontains=search)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [IsReadOnlyOrCollectionAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = Collection.objects.select_related(
            "organization",
            "created_by_member",
            "created_by_member__user",
            "branch",
            "geodata",
            "geodata__city",
            "geodata__city__region",
        ).prefetch_related("items", "items__category")

        organization_id = self.request.query_params.get("organization")
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        organization = serializer.validated_data["organization"]
        member = OrganizationMember.objects.get(
            organization=organization,
            user=self.request.user,
            is_active=True,
        )
        serializer.save(created_by_member=member)


class CollectionItemViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionItemSerializer
    permission_classes = [IsReadOnlyOrCollectionItemAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = CollectionItem.objects.select_related(
            "collection",
            "collection__organization",
            "collection__created_by_member",
            "collection__created_by_member__user",
            "category",
        )
        collection_id = self.request.query_params.get("collection")
        if collection_id:
            queryset = queryset.filter(collection_id=collection_id)
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class BranchItemViewSet(viewsets.ModelViewSet):
    serializer_class = BranchItemSerializer
    permission_classes = [IsReadOnlyOrBranchItemOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = BranchItem.objects.select_related(
            "branch",
            "branch__organization",
            "category",
        )
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class DonorGroupViewSet(viewsets.ModelViewSet):
    serializer_class = DonorGroupSerializer
    permission_classes = [IsReadOnlyOrDonorGroupCollectionAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = DonorGroup.objects.select_related(
            "collection",
            "collection__organization",
            "collection__created_by_member",
            "collection__created_by_member__user",
            "created_by_member",
            "created_by_member__user",
        ).prefetch_related(
            "members",
            "members__user",
            "items",
            "items__user_item",
            "items__user_item__user",
            "items__user_item__category",
        )
        collection_id = self.request.query_params.get("collection")
        if collection_id:
            queryset = queryset.filter(collection_id=collection_id)
        return queryset

    def perform_create(self, serializer):
        collection = serializer.validated_data["collection"]
        member = OrganizationMember.objects.get(
            organization=collection.organization,
            user=self.request.user,
            is_active=True,
        )
        serializer.save(created_by_member=member)


class DonorGroupMemberViewSet(viewsets.ModelViewSet):
    serializer_class = DonorGroupMemberSerializer
    permission_classes = [IsReadOnlyOrDonorGroupMemberManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = DonorGroupMember.objects.select_related(
            "donor_group",
            "donor_group__collection",
            "donor_group__collection__organization",
            "donor_group__collection__created_by_member",
            "donor_group__collection__created_by_member__user",
            "user",
        )
        donor_group_id = self.request.query_params.get("donor_group")
        if donor_group_id:
            queryset = queryset.filter(donor_group_id=donor_group_id)
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset


class DonorGroupItemViewSet(viewsets.ModelViewSet):
    serializer_class = DonorGroupItemSerializer
    permission_classes = [IsReadOnlyOrDonorGroupItemManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = DonorGroupItem.objects.select_related(
            "donor_group",
            "donor_group__collection",
            "donor_group__collection__organization",
            "donor_group__collection__created_by_member",
            "donor_group__collection__created_by_member__user",
            "user_item",
            "user_item__user",
            "user_item__category",
        )
        donor_group_id = self.request.query_params.get("donor_group")
        if donor_group_id:
            queryset = queryset.filter(donor_group_id=donor_group_id)
        user_item_id = self.request.query_params.get("user_item")
        if user_item_id:
            queryset = queryset.filter(user_item_id=user_item_id)
        return queryset


class CourierProfileViewSet(viewsets.ModelViewSet):
    serializer_class = CourierProfileSerializer
    permission_classes = [IsReadOnlyOrCourierProfileOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = CourierProfile.objects.select_related("user")
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

    def perform_create(self, serializer):
        if CourierProfile.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError(
                {"user": "Courier profile already exists for this user."}
            )
        serializer.save(user=self.request.user)
