from rest_framework import serializers

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


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "created_at")
        read_only_fields = fields


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "id",
            "official_name",
            "legal_address",
            "phone",
            "email",
            "max_url",
            "vk_url",
            "website_url",
            "executive_person_full_name",
            "executive_authority_basis",
            "executive_body_name",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    organization_name = serializers.CharField(
        source="organization.official_name",
        read_only=True,
    )

    class Meta:
        model = OrganizationMember
        fields = (
            "id",
            "organization",
            "organization_name",
            "user",
            "user_email",
            "user_full_name",
            "role",
            "is_active",
            "removed_at",
            "removed_by",
            "created_at",
        )
        read_only_fields = fields


class OrganizationBranchImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationBranchImage
        fields = ("id", "branch", "image", "alt_text", "sort_order", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_branch(self, branch):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        if not OrganizationMember.objects.filter(
            organization=branch.organization,
            user=user,
            role=OrganizationMember.Role.MANAGER,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "Only an active organization manager can add branch images."
            )
        return branch

    def validate(self, attrs):
        if self.instance and "branch" in attrs and attrs["branch"] != self.instance.branch:
            raise serializers.ValidationError({"branch": "Branch cannot be changed."})
        return attrs


class OrganizationBranchSerializer(serializers.ModelSerializer):
    images = OrganizationBranchImageSerializer(many=True, read_only=True)
    images_count = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationBranch
        fields = (
            "id",
            "organization",
            "geodata",
            "name",
            "description",
            "phone",
            "email",
            "working_hours",
            "is_active",
            "images",
            "images_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "images", "images_count", "created_at", "updated_at")

    def get_images_count(self, obj):
        return obj.images.count()

    def validate_organization(self, organization):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        if not OrganizationMember.objects.filter(
            organization=organization,
            user=user,
            role=OrganizationMember.Role.MANAGER,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "Only an active organization manager can manage branches."
            )
        return organization

    def validate(self, attrs):
        if self.instance and "organization" in attrs and attrs["organization"] != self.instance.organization:
            raise serializers.ValidationError({"organization": "Organization cannot be changed."})
        return attrs


class EventSerializer(serializers.ModelSerializer):
    created_by_member = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "slug",
            "content",
            "image",
            "category",
            "organization",
            "geodata",
            "created_by_member",
            "status",
            "starts_at",
            "ends_at",
            "city",
            "is_online",
            "max_url",
            "vk_url",
            "website_url",
            "created_at",
            "updated_at",
            "published_at",
        )
        read_only_fields = ("id", "slug", "created_by_member", "created_at", "updated_at")

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
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at and ends_at and ends_at < starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End date cannot be earlier than start date."}
            )
        return attrs


class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ("id", "event", "image", "alt_text", "sort_order", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_event(self, event):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        if not OrganizationMember.objects.filter(
            organization=event.organization,
            user=user,
            is_active=True,
        ).exists():
            raise serializers.ValidationError("User is not an active member of this organization.")
        return event

    def validate(self, attrs):
        if self.instance and "event" in attrs and attrs["event"] != self.instance.event:
            raise serializers.ValidationError({"event": "Event cannot be changed."})
        return attrs


class OrganizationNewsImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationNewsImage
        fields = ("id", "news", "image", "alt_text", "sort_order", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_news(self, news):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        if news.created_by_member.user_id == user.id and news.created_by_member.is_active:
            return news
        if OrganizationMember.objects.filter(
            organization=news.organization,
            user=user,
            role=OrganizationMember.Role.MANAGER,
            is_active=True,
        ).exists():
            return news
        raise serializers.ValidationError(
            "Only the news author or an organization manager can add images."
        )

    def validate(self, attrs):
        if self.instance and "news" in attrs and attrs["news"] != self.instance.news:
            raise serializers.ValidationError({"news": "News cannot be changed."})
        return attrs


class OrganizationNewsSerializer(serializers.ModelSerializer):
    created_by_member = serializers.PrimaryKeyRelatedField(read_only=True)
    images = OrganizationNewsImageSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    images_count = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationNews
        fields = (
            "id",
            "organization",
            "created_by_member",
            "title",
            "text",
            "image",
            "images",
            "comments",
            "comments_count",
            "images_count",
            "views_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by_member",
            "images",
            "comments_count",
            "images_count",
            "views_count",
            "created_at",
            "updated_at",
        )

    def get_comments_count(self, obj):
        return obj.comment_items.count()

    def get_images_count(self, obj):
        return obj.images.count()

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
        return attrs


EventNewsSerializer = OrganizationNewsSerializer


class OrganizationNewsCommentSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = OrganizationNewsComment
        fields = (
            "id",
            "news",
            "created_by",
            "created_by_email",
            "text",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_by_email", "created_at", "updated_at")

    def validate(self, attrs):
        if self.instance and "news" in attrs and attrs["news"] != self.instance.news:
            raise serializers.ValidationError({"news": "News cannot be changed."})
        return attrs


class OrganizationRegistrationRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationRegistrationRequest
        exclude = (
            "created_by",
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "organization",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class OrganizationRegistrationRequestReadSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    reviewed_by_email = serializers.EmailField(
        source="reviewed_by.email",
        read_only=True,
        allow_null=True,
    )
    organization_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = OrganizationRegistrationRequest
        fields = (
            "id",
            "created_by",
            "created_by_email",
            "official_name",
            "legal_address",
            "phone",
            "email",
            "max_url",
            "vk_url",
            "website_url",
            "executive_person_full_name",
            "executive_authority_basis",
            "executive_body_name",
            "charter_document",
            "inn_certificate",
            "state_registration_certificate",
            "founders_appointment_decision",
            "executive_passport_copy",
            "egrul_extract",
            "nko_registry_notice",
            "status",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "rejection_reason",
            "organization",
            "organization_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrganizationRegistrationDecisionSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True, allow_blank=False)
