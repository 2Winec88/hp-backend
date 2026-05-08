from rest_framework import serializers

from apps.organizations.models import OrganizationMember
from apps.organizations.permissions import is_active_organization_manager

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
    is_collection_author_or_manager,
    is_donor_group_collection_author_or_manager,
)


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = (
            "id",
            "name",
            "description",
            "unit",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class UserItemSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = UserItem
        fields = (
            "id",
            "user",
            "user_email",
            "category",
            "category_name",
            "quantity",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "user_email", "category_name", "created_at", "updated_at")


class CollectionItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = CollectionItem
        fields = (
            "id",
            "collection",
            "category",
            "category_name",
            "quantity_required",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "category_name", "created_at", "updated_at")

    def validate_collection(self, collection):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_collection_author_or_manager(collection=collection, user=user):
            raise serializers.ValidationError(
                "Only the collection author or an organization manager can manage collection items."
            )
        return collection

    def validate(self, attrs):
        if self.instance and "collection" in attrs and attrs["collection"] != self.instance.collection:
            raise serializers.ValidationError({"collection": "Collection cannot be changed."})
        return attrs


class CollectionSerializer(serializers.ModelSerializer):
    created_by_member = serializers.PrimaryKeyRelatedField(read_only=True)
    organization_name = serializers.CharField(source="organization.official_name", read_only=True)
    items = CollectionItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = (
            "id",
            "organization",
            "organization_name",
            "created_by_member",
            "branch",
            "geodata",
            "title",
            "description",
            "status",
            "starts_at",
            "ends_at",
            "items",
            "items_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "organization_name",
            "created_by_member",
            "items",
            "items_count",
            "created_at",
            "updated_at",
        )

    def get_items_count(self, obj):
        return obj.items.count()

    def validate_organization(self, organization):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        if not OrganizationMember.objects.filter(
            organization=organization,
            user=user,
            is_active=True,
        ).exists():
            raise serializers.ValidationError("User is not an active member of this organization.")
        return organization

    def validate(self, attrs):
        if self.instance and "organization" in attrs and attrs["organization"] != self.instance.organization:
            raise serializers.ValidationError({"organization": "Organization cannot be changed."})

        organization = attrs.get("organization", getattr(self.instance, "organization", None))
        branch = attrs.get("branch", getattr(self.instance, "branch", None))
        if branch and organization and branch.organization_id != organization.id:
            raise serializers.ValidationError(
                {"branch": "Branch must belong to the collection organization."}
            )

        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at and ends_at and ends_at < starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End date cannot be earlier than start date."}
            )

        return attrs


class BranchItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = BranchItem
        fields = (
            "id",
            "branch",
            "category",
            "category_name",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "category_name", "created_at", "updated_at")

    def validate_branch(self, branch):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        if not is_active_organization_manager(organization=branch.organization, user=user):
            raise serializers.ValidationError(
                "Only an active organization manager can manage branch items."
            )
        return branch

    def validate(self, attrs):
        if self.instance and "branch" in attrs and attrs["branch"] != self.instance.branch:
            raise serializers.ValidationError({"branch": "Branch cannot be changed."})
        return attrs


class DonorGroupMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = DonorGroupMember
        fields = (
            "id",
            "donor_group",
            "user",
            "user_email",
            "joined_at",
        )
        read_only_fields = ("id", "user_email", "joined_at")

    def validate_donor_group(self, donor_group):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_donor_group_collection_author_or_manager(
            donor_group=donor_group,
            user=user,
        ):
            raise serializers.ValidationError(
                "Only the collection author or an organization manager can manage donor group members."
            )
        return donor_group

    def validate(self, attrs):
        if self.instance and "donor_group" in attrs and attrs["donor_group"] != self.instance.donor_group:
            raise serializers.ValidationError({"donor_group": "Donor group cannot be changed."})
        if self.instance and "user" in attrs and attrs["user"] != self.instance.user:
            raise serializers.ValidationError({"user": "User cannot be changed."})
        return attrs


class DonorGroupItemSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(source="user_item.user", read_only=True)
    category = serializers.PrimaryKeyRelatedField(source="user_item.category", read_only=True)
    category_name = serializers.CharField(source="user_item.category.name", read_only=True)

    class Meta:
        model = DonorGroupItem
        fields = (
            "id",
            "donor_group",
            "user_item",
            "user",
            "category",
            "category_name",
            "quantity",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "category", "category_name", "created_at", "updated_at")

    def validate_donor_group(self, donor_group):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_donor_group_collection_author_or_manager(
            donor_group=donor_group,
            user=user,
        ):
            raise serializers.ValidationError(
                "Only the collection author or an organization manager can manage donor group items."
            )
        return donor_group

    def validate(self, attrs):
        if self.instance and "donor_group" in attrs and attrs["donor_group"] != self.instance.donor_group:
            raise serializers.ValidationError({"donor_group": "Donor group cannot be changed."})

        user_item = attrs.get("user_item", getattr(self.instance, "user_item", None))
        donor_group = attrs.get("donor_group", getattr(self.instance, "donor_group", None))
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        if user_item and quantity and quantity > user_item.quantity:
            raise serializers.ValidationError(
                {"quantity": "Selected quantity cannot exceed the user's item quantity."}
            )
        if (
            donor_group
            and user_item
            and not DonorGroupMember.objects.filter(
                donor_group=donor_group,
                user=user_item.user,
            ).exists()
        ):
            raise serializers.ValidationError(
                {"user_item": "The user item owner must be a donor group member."}
            )
        return attrs


class DonorGroupSerializer(serializers.ModelSerializer):
    created_by_member = serializers.PrimaryKeyRelatedField(read_only=True)
    members = DonorGroupMemberSerializer(many=True, read_only=True)
    items = DonorGroupItemSerializer(many=True, read_only=True)
    members_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = DonorGroup
        fields = (
            "id",
            "collection",
            "created_by_member",
            "title",
            "members",
            "items",
            "members_count",
            "items_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by_member",
            "members",
            "items",
            "members_count",
            "items_count",
            "created_at",
            "updated_at",
        )

    def get_members_count(self, obj):
        return obj.members.count()

    def get_items_count(self, obj):
        return obj.items.count()

    def validate_collection(self, collection):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_collection_author_or_manager(collection=collection, user=user):
            raise serializers.ValidationError(
                "Only the collection author or an organization manager can manage donor groups."
            )
        return collection

    def validate(self, attrs):
        if self.instance and "collection" in attrs and attrs["collection"] != self.instance.collection:
            raise serializers.ValidationError({"collection": "Collection cannot be changed."})
        return attrs


class CourierProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CourierProfile
        fields = (
            "id",
            "user",
            "user_email",
            "car_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "user_email", "created_at", "updated_at")
