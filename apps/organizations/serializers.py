from rest_framework import serializers

from .models import OrganizationRegistrationRequest


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
