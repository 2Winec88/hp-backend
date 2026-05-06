from rest_framework import serializers

from .models import Category, Event, EventNews, OrganizationMember, OrganizationRegistrationRequest


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
            "created_by_member",
            "status",
            "starts_at",
            "ends_at",
            "city",
            "is_online",
            "created_at",
            "updated_at",
            "published_at",
        )
        read_only_fields = ("id", "slug", "created_by_member", "created_at", "updated_at")

    def validate_category(self, category):
        if category.scope != Category.Scope.EVENT:
            raise serializers.ValidationError("Event category is required.")
        return category

    def validate_organization(self, organization):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        if not OrganizationMember.objects.filter(
            organization=organization,
            user=user,
        ).exists():
            raise serializers.ValidationError("User is not a member of this organization.")
        return organization

    def validate(self, attrs):
        if self.instance and "organization" in attrs and attrs["organization"] != self.instance.organization:
            raise serializers.ValidationError({"organization": "Organization cannot be changed."})
        return attrs


class EventNewsSerializer(serializers.ModelSerializer):
    created_by_member = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EventNews
        fields = (
            "id",
            "event",
            "created_by_member",
            "title",
            "text",
            "image",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by_member", "created_at", "updated_at")

    def validate_event(self, event):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        if not OrganizationMember.objects.filter(
            organization=event.organization,
            user=user,
        ).exists():
            raise serializers.ValidationError("User is not a member of this event organization.")
        return event

    def validate(self, attrs):
        if self.instance and "event" in attrs and attrs["event"] != self.instance.event:
            raise serializers.ValidationError({"event": "Event cannot be changed."})
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
