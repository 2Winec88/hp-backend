from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Organization, OrganizationMember, OrganizationRegistrationRequest


def _ensure_request_is_pending(registration_request):
    if registration_request.status != OrganizationRegistrationRequest.Status.PENDING:
        raise ValidationError("Only pending requests can be processed.")


@transaction.atomic
def approve_organization_registration_request(*, registration_request, reviewer):
    registration_request = (
        OrganizationRegistrationRequest.objects.select_for_update()
        .select_related("created_by")
        .get(pk=registration_request.pk)
    )
    _ensure_request_is_pending(registration_request)

    if registration_request.organization_id is not None:
        raise ValidationError("Organization has already been created for this request.")

    organization = Organization.objects.create(
        created_by=registration_request.created_by,
        official_name=registration_request.official_name,
        legal_address=registration_request.legal_address,
        phone=registration_request.phone,
        email=registration_request.email,
        executive_person_full_name=registration_request.executive_person_full_name,
        executive_authority_basis=registration_request.executive_authority_basis,
        executive_body_name=registration_request.executive_body_name,
    )
    OrganizationMember.objects.get_or_create(
        organization=organization,
        user=registration_request.created_by,
        defaults={"role": OrganizationMember.Role.MANAGER},
    )

    registration_request.status = OrganizationRegistrationRequest.Status.APPROVED
    registration_request.reviewed_by = reviewer
    registration_request.reviewed_at = timezone.now()
    registration_request.rejection_reason = ""
    registration_request.organization = organization
    registration_request.save(
        update_fields=(
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "organization",
            "updated_at",
        )
    )
    return registration_request


def reject_organization_registration_request(*, registration_request, reviewer, rejection_reason):
    _ensure_request_is_pending(registration_request)

    registration_request.status = OrganizationRegistrationRequest.Status.REJECTED
    registration_request.reviewed_by = reviewer
    registration_request.reviewed_at = timezone.now()
    registration_request.rejection_reason = rejection_reason
    registration_request.save(
        update_fields=(
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        )
    )
    return registration_request
