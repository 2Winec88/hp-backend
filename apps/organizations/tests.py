from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Role, UserRole
from apps.core.models import Category

from .models import (
    Event,
    Organization,
    OrganizationCommonFieldsMixin,
    OrganizationMember,
    OrganizationRegistrationRequest,
)


def create_test_file(name):
    return SimpleUploadedFile(name, b"file-content", content_type="application/pdf")


class OrganizationModelStructureTests(SimpleTestCase):
    def test_organization_models_share_common_fields_mixin(self):
        self.assertTrue(OrganizationCommonFieldsMixin._meta.abstract)
        self.assertTrue(issubclass(Organization, OrganizationCommonFieldsMixin))
        self.assertTrue(issubclass(OrganizationRegistrationRequest, OrganizationCommonFieldsMixin))

        common_fields = {
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
            "created_at",
            "updated_at",
        }
        self.assertLessEqual(common_fields, {field.name for field in Organization._meta.fields})
        self.assertLessEqual(
            common_fields,
            {field.name for field in OrganizationRegistrationRequest._meta.fields},
        )


class EventModelTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="event-author",
            email="event-author@example.com",
            password="StrongPassword123!",
        )
        self.organization = Organization.objects.create(
            created_by=self.user,
            official_name="Event Org",
            legal_address="Address",
            phone="+7 777 000 00 00",
            email="org@example.com",
            executive_person_full_name="Executive Person",
            executive_authority_basis="Charter",
            executive_body_name="Board",
            charter_document="charter.pdf",
            inn_certificate="inn.pdf",
            state_registration_certificate="registration.pdf",
            founders_appointment_decision="founders.pdf",
            executive_passport_copy="passport.pdf",
            egrul_extract="egrul.pdf",
            nko_registry_notice="registry.pdf",
        )
        self.member = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMember.Role.MANAGER,
        )
        self.event_category = Category.objects.create(
            name="Спорт",
            scope=Category.Scope.EVENT,
        )

    def test_event_generates_slug_from_title(self):
        event = Event.objects.create(
            title="Полумарафон Оренбург-2026",
            content="Описание мероприятия",
            category=self.event_category,
            organization=self.organization,
            created_by_member=self.member,
            starts_at=timezone.now(),
        )

        self.assertEqual(event.slug, "полумарафон-оренбург-2026")
        self.assertEqual(str(event), "Полумарафон Оренбург-2026")

    def test_event_rejects_non_event_category(self):
        fundraising_category = Category.objects.create(
            name="Сборы спорт",
            scope=Category.Scope.FUNDRAISING,
        )
        event = Event(
            title="Полумарафон",
            content="Описание мероприятия",
            category=fundraising_category,
            organization=self.organization,
            created_by_member=self.member,
            starts_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_event_rejects_member_from_another_organization(self):
        other_user = self.user_model.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123!",
        )
        other_organization = Organization.objects.create(
            created_by=other_user,
            official_name="Other Org",
            legal_address="Other Address",
            phone="+7 777 000 00 01",
            email="other-org@example.com",
            executive_person_full_name="Other Executive",
            executive_authority_basis="Charter",
            executive_body_name="Board",
            charter_document="charter.pdf",
            inn_certificate="inn.pdf",
            state_registration_certificate="registration.pdf",
            founders_appointment_decision="founders.pdf",
            executive_passport_copy="passport.pdf",
            egrul_extract="egrul.pdf",
            nko_registry_notice="registry.pdf",
        )
        other_member = OrganizationMember.objects.create(
            organization=other_organization,
            user=other_user,
            role=OrganizationMember.Role.MANAGER,
        )
        event = Event(
            title="Полумарафон",
            content="Описание мероприятия",
            category=self.event_category,
            organization=self.organization,
            created_by_member=other_member,
            starts_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            event.full_clean()


class OrganizationRegistrationRequestApiTests(APITestCase):
    url = "/api/v1/organizations/organization-registration-requests/"

    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="user",
            email="user@example.com",
            password="StrongPassword123!",
        )
        self.other_user = self.user_model.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.moderator = self.user_model.objects.create_user(
            username="moderator",
            email="moderator@example.com",
            password="StrongPassword123!",
        )
        self.moderator_role = Role.objects.create(
            name="Moderator",
            code="moderator",
        )
        UserRole.objects.create(user=self.moderator, role=self.moderator_role)

    def _payload(self, suffix="1"):
        return {
            "official_name": f"Фонд {suffix}",
            "legal_address": "г. Алматы, ул. Абая, 1",
            "phone": "+7 777 000 00 00",
            "email": f"fund{suffix}@example.com",
            "executive_person_full_name": "Иванов Иван Иванович",
            "executive_authority_basis": "Устав",
            "executive_body_name": "Директор",
            "charter_document": create_test_file(f"charter-{suffix}.pdf"),
            "inn_certificate": create_test_file(f"inn-{suffix}.pdf"),
            "state_registration_certificate": create_test_file(f"registration-{suffix}.pdf"),
            "founders_appointment_decision": create_test_file(f"founders-{suffix}.pdf"),
            "executive_passport_copy": create_test_file(f"passport-{suffix}.pdf"),
            "egrul_extract": create_test_file(f"egrul-{suffix}.pdf"),
            "nko_registry_notice": create_test_file(f"registry-{suffix}.pdf"),
        }

    def _create_request(self, user=None, suffix="1"):
        request_user = user or self.user
        self.client.force_authenticate(request_user)
        response = self.client.post(self.url, data=self._payload(suffix), format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(None)
        return OrganizationRegistrationRequest.objects.get(pk=response.data["id"])

    def test_user_can_create_registration_request(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, data=self._payload(), format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        registration_request = OrganizationRegistrationRequest.objects.get(pk=response.data["id"])
        self.assertEqual(registration_request.created_by, self.user)
        self.assertEqual(registration_request.status, OrganizationRegistrationRequest.Status.PENDING)

    def test_user_cannot_view_another_users_request(self):
        foreign_request = self._create_request(user=self.other_user, suffix="2")
        self.client.force_authenticate(self.user)

        response = self.client.get(f"{self.url}{foreign_request.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_moderator_sees_all_requests(self):
        self._create_request(user=self.user, suffix="3")
        self._create_request(user=self.other_user, suffix="4")
        self.client.force_authenticate(self.moderator)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_moderator_can_approve_pending_request(self):
        registration_request = self._create_request()
        self.client.force_authenticate(self.moderator)

        response = self.client.post(f"{self.url}{registration_request.pk}/approve/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        registration_request.refresh_from_db()
        organization = Organization.objects.get(pk=registration_request.organization_id)
        membership = OrganizationMember.objects.get(
            organization=organization,
            user=self.user,
        )
        self.assertEqual(registration_request.status, OrganizationRegistrationRequest.Status.APPROVED)
        self.assertEqual(registration_request.reviewed_by, self.moderator)
        self.assertEqual(organization.created_by, self.user)
        self.assertEqual(organization.official_name, registration_request.official_name)
        self.assertEqual(membership.role, OrganizationMember.Role.MANAGER)

    def test_moderator_can_reject_pending_request(self):
        registration_request = self._create_request(suffix="5")
        self.client.force_authenticate(self.moderator)

        response = self.client.post(
            f"{self.url}{registration_request.pk}/reject/",
            data={"rejection_reason": "Недостаточно документов"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        registration_request.refresh_from_db()
        self.assertEqual(registration_request.status, OrganizationRegistrationRequest.Status.REJECTED)
        self.assertEqual(registration_request.rejection_reason, "Недостаточно документов")

    def test_cannot_approve_rejected_request(self):
        registration_request = self._create_request(suffix="6")
        registration_request.status = OrganizationRegistrationRequest.Status.REJECTED
        registration_request.rejection_reason = "Уже отклонено"
        registration_request.save(update_fields=("status", "rejection_reason", "updated_at"))
        self.client.force_authenticate(self.moderator)

        response = self.client.post(f"{self.url}{registration_request.pk}/approve/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_reject_approved_request(self):
        registration_request = self._create_request(suffix="7")
        registration_request.status = OrganizationRegistrationRequest.Status.APPROVED
        registration_request.save(update_fields=("status", "updated_at"))
        self.client.force_authenticate(self.moderator)

        response = self.client.post(
            f"{self.url}{registration_request.pk}/reject/",
            data={"rejection_reason": "Поздно"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
