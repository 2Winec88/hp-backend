from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.models import City, GeoData

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


def create_test_file(name):
    return SimpleUploadedFile(name, b"file-content", content_type="application/pdf")


def create_test_image_file(name="image.gif"):
    return SimpleUploadedFile(
        name,
        (
            b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xff\xff\xff,\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02D\x01\x00;"
        ),
        content_type="image/gif",
    )


class OrganizationModelStructureTests(SimpleTestCase):
    def test_registration_request_stores_documents_without_duplicating_them_in_organization(self):
        common_fields = {
            "official_name",
            "legal_address",
            "phone",
            "email",
            "executive_person_full_name",
            "executive_authority_basis",
            "executive_body_name",
            "created_at",
            "updated_at",
        }
        document_fields = {
            "charter_document",
            "inn_certificate",
            "state_registration_certificate",
            "founders_appointment_decision",
            "executive_passport_copy",
            "egrul_extract",
            "nko_registry_notice",
        }
        organization_fields = {field.name for field in Organization._meta.fields}
        registration_request_fields = {
            field.name for field in OrganizationRegistrationRequest._meta.fields
        }

        self.assertLessEqual(common_fields, organization_fields)
        self.assertLessEqual(
            common_fields | document_fields,
            registration_request_fields,
        )
        self.assertTrue(document_fields.isdisjoint(organization_fields))


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
        )
        self.member = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMember.Role.MANAGER,
        )
        self.event_category = Category.objects.create(
            name="Спорт",
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

    def test_event_can_have_multiple_images(self):
        event = Event.objects.create(
            title="Gallery Event",
            content="Event with several images",
            category=self.event_category,
            organization=self.organization,
            created_by_member=self.member,
            starts_at=timezone.now(),
        )

        first_image = EventImage.objects.create(
            event=event,
            image="first.jpg",
            alt_text="First image",
            sort_order=2,
        )
        second_image = EventImage.objects.create(
            event=event,
            image="second.jpg",
            alt_text="Second image",
            sort_order=1,
        )

        self.assertEqual(event.images.count(), 2)
        self.assertEqual(list(event.images.all()), [second_image, first_image])

    def test_event_can_have_news_with_image_and_text(self):
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member,
            title="Маршрут обновлён",
            text="Добавили новую точку старта.",
            image="route.jpg",
        )

        self.assertEqual(self.organization.news.count(), 1)
        self.assertEqual(self.organization.news.get(), news)
        self.assertEqual(str(news), "Маршрут обновлён")

    def test_all_users_can_view_organization_news(self):
        OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member,
            title="Открытая новость",
            text="Её видят все.",
            image="public.jpg",
        )

        response = self.client.get("/api/v1/organizations/news/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_only_news_author_or_organization_manager_can_edit_organization_news(self):
        author = self.user_model.objects.create_user(
            username="news-author",
            email="news-author@example.com",
            password="StrongPassword123!",
        )
        author_member = OrganizationMember.objects.create(
            organization=self.organization,
            user=author,
            role=OrganizationMember.Role.MEMBER,
        )
        outsider = self.user_model.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="StrongPassword123!",
        )
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=author_member,
            title="Исходная новость",
            text="Текст.",
            image="editable.jpg",
        )

        self.client.force_authenticate(outsider)
        response = self.client.patch(
            f"/api/v1/organizations/news/{news.pk}/",
            data={"title": "Чужая правка"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(author)
        response = self.client.patch(
            f"/api/v1/organizations/news/{news.pk}/",
            data={"title": "Правка автора"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/v1/organizations/news/{news.pk}/",
            data={"title": "Правка менеджера"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_organization_news_detail_increments_views_count(self):
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member,
            title="Viewed News",
            text="Text",
        )

        response = self.client.get(f"/api/v1/organizations/news/{news.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["views_count"], 1)
        news.refresh_from_db()
        self.assertEqual(news.views_count, 1)

    def test_authenticated_user_can_comment_organization_news(self):
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member,
            title="Commented News",
            text="Text",
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/v1/organizations/news-comments/",
            data={"news": news.pk, "text": "Nice update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = OrganizationNewsComment.objects.get(pk=response.data["id"])
        self.assertEqual(comment.created_by, self.user)
        self.assertEqual(comment.news, news)

    def test_comment_news_cannot_be_changed(self):
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member,
            title="First News",
            text="Text",
        )
        other_news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member,
            title="Second News",
            text="Text",
        )
        comment = OrganizationNewsComment.objects.create(
            news=news,
            created_by=self.user,
            text="Initial comment",
        )
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            f"/api/v1/organizations/news-comments/{comment.pk}/",
            data={"news": other_news.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        comment.refresh_from_db()
        self.assertEqual(comment.news, news)

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


class OrganizationAdministrationApiTests(APITestCase):
    members_url = "/api/v1/organizations/members/"
    events_url = "/api/v1/organizations/events/"
    news_url = "/api/v1/organizations/news/"
    organizations_url = "/api/v1/organizations/organizations/"
    categories_url = "/api/v1/organizations/categories/"
    branches_url = "/api/v1/organizations/branches/"
    branch_images_url = "/api/v1/organizations/branch-images/"
    event_images_url = "/api/v1/organizations/event-images/"
    news_images_url = "/api/v1/organizations/news-images/"

    def setUp(self):
        self.user_model = get_user_model()
        self.manager = self.user_model.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="StrongPassword123!",
        )
        self.member_user = self.user_model.objects.create_user(
            username="member",
            email="member@example.com",
            password="StrongPassword123!",
        )
        self.outsider = self.user_model.objects.create_user(
            username="outsider-admin",
            email="outsider-admin@example.com",
            password="StrongPassword123!",
        )
        self.organization = Organization.objects.create(
            created_by=self.manager,
            official_name="Admin Org",
            legal_address="Address",
            phone="+7 777 000 00 00",
            email="admin-org@example.com",
            executive_person_full_name="Executive Person",
            executive_authority_basis="Charter",
            executive_body_name="Board",
        )
        self.manager_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.manager,
            role=OrganizationMember.Role.MANAGER,
        )
        self.member_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.member_user,
            role=OrganizationMember.Role.MEMBER,
        )
        self.event_category = Category.objects.create(name="Admin Category")
        self.city, _ = City.objects.get_or_create(
            name="Yekaterinburg",
        )
        self.geodata = GeoData.objects.create(
            city=self.city,
            street="Lenina, 1",
            latitude="56.838011",
            longitude="60.597465",
        )

    def test_manager_can_exclude_organization_member(self):
        self.client.force_authenticate(self.manager)

        response = self.client.delete(f"{self.members_url}{self.member_membership.pk}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.member_membership.refresh_from_db()
        self.assertFalse(self.member_membership.is_active)
        self.assertIsNotNone(self.member_membership.removed_at)
        self.assertEqual(self.member_membership.removed_by, self.manager)

    def test_non_manager_cannot_exclude_organization_member(self):
        self.client.force_authenticate(self.member_user)

        response = self.client.delete(f"{self.members_url}{self.manager_membership.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            OrganizationMember.objects.filter(pk=self.manager_membership.pk).exists()
        )

    def test_manager_cannot_remove_self_from_organization(self):
        self.client.force_authenticate(self.manager)

        response = self.client.delete(f"{self.members_url}{self.manager_membership.pk}/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            OrganizationMember.objects.filter(pk=self.manager_membership.pk).exists()
        )

    def test_excluding_member_does_not_delete_member_content(self):
        event = Event.objects.create(
            title="Member Event",
            content="Created by member",
            category=self.event_category,
            organization=self.organization,
            created_by_member=self.member_membership,
            starts_at=timezone.now(),
        )
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member_membership,
            title="Member News",
            text="Created by member",
        )
        self.client.force_authenticate(self.manager)

        response = self.client.delete(f"{self.members_url}{self.member_membership.pk}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Event.objects.filter(pk=event.pk).exists())
        self.assertTrue(OrganizationNews.objects.filter(pk=news.pk).exists())
        self.member_membership.refresh_from_db()
        self.assertFalse(self.member_membership.is_active)

    def test_inactive_member_cannot_create_event(self):
        self.member_membership.is_active = False
        self.member_membership.removed_at = timezone.now()
        self.member_membership.removed_by = self.manager
        self.member_membership.save(
            update_fields=("is_active", "removed_at", "removed_by")
        )
        self.client.force_authenticate(self.member_user)

        response = self.client.post(
            self.events_url,
            data={
                "title": "Inactive Member Event",
                "content": "Should be rejected",
                "category": self.event_category.pk,
                "organization": self.organization.pk,
                "starts_at": timezone.now().isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_can_edit_and_delete_member_event(self):
        event = Event.objects.create(
            title="Member Event",
            content="Created by member",
            category=self.event_category,
            organization=self.organization,
            created_by_member=self.member_membership,
            starts_at=timezone.now(),
        )
        self.client.force_authenticate(self.manager)

        patch_response = self.client.patch(
            f"{self.events_url}{event.pk}/",
            data={"title": "Manager Edited Event"},
            format="json",
        )
        delete_response = self.client.delete(f"{self.events_url}{event.pk}/")

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(pk=event.pk).exists())

    def test_event_api_exposes_event_social_links(self):
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            self.events_url,
            data={
                "title": "Linked Event",
                "content": "Event with external links",
                "category": self.event_category.pk,
                "organization": self.organization.pk,
                "geodata": self.geodata.pk,
                "starts_at": timezone.now().isoformat(),
                "max_url": "https://max.example.com/event-post",
                "vk_url": "https://vk.com/event-post",
                "website_url": "https://events.example.com/linked-event",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["geodata"], self.geodata.pk)
        self.assertEqual(response.data["max_url"], "https://max.example.com/event-post")
        self.assertEqual(response.data["vk_url"], "https://vk.com/event-post")
        self.assertEqual(response.data["website_url"], "https://events.example.com/linked-event")

    def test_event_api_rejects_end_before_start(self):
        self.client.force_authenticate(self.manager)
        starts_at = timezone.now()

        response = self.client.post(
            self.events_url,
            data={
                "title": "Invalid Event Dates",
                "content": "Dates are invalid",
                "category": self.event_category.pk,
                "organization": self.organization.pk,
                "starts_at": starts_at.isoformat(),
                "ends_at": (starts_at - timedelta(hours=1)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ends_at", response.data)

    def test_manager_can_update_organization(self):
        self.client.force_authenticate(self.manager)

        response = self.client.patch(
            f"{self.organizations_url}{self.organization.pk}/",
            data={"vk_url": "https://vk.com/admin-org"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.vk_url, "https://vk.com/admin-org")

    def test_categories_are_read_only_in_api(self):
        self.client.force_authenticate(self.manager)

        list_response = self.client.get(self.categories_url)
        create_response = self.client.post(
            self.categories_url,
            data={"name": "Forbidden Category"},
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(create_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_manager_can_create_branch_with_geodata(self):
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            self.branches_url,
            data={
                "organization": self.organization.pk,
                "geodata": self.geodata.pk,
                "name": "Central Branch",
                "description": "Main donation point",
                "phone": "+7 777 000 00 02",
                "email": "branch@example.com",
                "working_hours": "Mon-Fri 10:00-19:00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        branch = OrganizationBranch.objects.get(pk=response.data["id"])
        self.assertEqual(branch.organization, self.organization)
        self.assertEqual(branch.geodata, self.geodata)
        self.assertEqual(response.data["images_count"], 0)

    def test_all_users_can_view_branches(self):
        OrganizationBranch.objects.create(
            organization=self.organization,
            geodata=self.geodata,
            name="Public Branch",
            description="Visible to everyone",
        )

        response = self.client.get(self.branches_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_only_manager_can_manage_branches(self):
        branch = OrganizationBranch.objects.create(
            organization=self.organization,
            geodata=self.geodata,
            name="Protected Branch",
            description="Managed by managers",
        )

        self.client.force_authenticate(self.member_user)
        member_create_response = self.client.post(
            self.branches_url,
            data={
                "organization": self.organization.pk,
                "name": "Member Branch",
            },
            format="json",
        )
        self.assertEqual(member_create_response.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(self.outsider)
        outsider_patch_response = self.client.patch(
            f"{self.branches_url}{branch.pk}/",
            data={"name": "Outsider Edit"},
            format="json",
        )
        self.assertEqual(outsider_patch_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.manager)
        manager_patch_response = self.client.patch(
            f"{self.branches_url}{branch.pk}/",
            data={"name": "Manager Edit"},
            format="json",
        )
        self.assertEqual(manager_patch_response.status_code, status.HTTP_200_OK)

    def test_branch_organization_cannot_be_changed(self):
        other_organization = Organization.objects.create(
            created_by=self.manager,
            official_name="Other Branch Org",
            legal_address="Other Address",
            phone="+7 777 000 00 03",
            email="other-branch-org@example.com",
            executive_person_full_name="Other Executive",
            executive_authority_basis="Charter",
            executive_body_name="Board",
        )
        OrganizationMember.objects.create(
            organization=other_organization,
            user=self.manager,
            role=OrganizationMember.Role.MANAGER,
        )
        branch = OrganizationBranch.objects.create(
            organization=self.organization,
            name="Fixed Organization Branch",
        )
        self.client.force_authenticate(self.manager)

        response = self.client.patch(
            f"{self.branches_url}{branch.pk}/",
            data={"organization": other_organization.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        branch.refresh_from_db()
        self.assertEqual(branch.organization, self.organization)

    def test_branch_can_have_multiple_images(self):
        branch = OrganizationBranch.objects.create(
            organization=self.organization,
            name="Gallery Branch",
        )

        first_image = OrganizationBranchImage.objects.create(
            branch=branch,
            image="first.jpg",
            alt_text="First image",
            sort_order=2,
        )
        second_image = OrganizationBranchImage.objects.create(
            branch=branch,
            image="second.jpg",
            alt_text="Second image",
            sort_order=1,
        )

        self.assertEqual(branch.images.count(), 2)
        self.assertEqual(list(branch.images.all()), [second_image, first_image])

    def test_manager_can_manage_branch_images(self):
        branch = OrganizationBranch.objects.create(
            organization=self.organization,
            name="Image Branch",
        )
        self.client.force_authenticate(self.manager)

        create_response = self.client.post(
            self.branch_images_url,
            data={
                "branch": branch.pk,
                "image": create_test_image_file("branch.gif"),
                "alt_text": "Branch image",
                "sort_order": 1,
            },
            format="multipart",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        image = OrganizationBranchImage.objects.get(pk=create_response.data["id"])

        patch_response = self.client.patch(
            f"{self.branch_images_url}{image.pk}/",
            data={"alt_text": "Updated branch image"},
            format="json",
        )
        delete_response = self.client.delete(f"{self.branch_images_url}{image.pk}/")

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OrganizationBranchImage.objects.filter(pk=image.pk).exists())

    def test_non_manager_cannot_manage_branch_images(self):
        branch = OrganizationBranch.objects.create(
            organization=self.organization,
            name="Protected Image Branch",
        )
        image = OrganizationBranchImage.objects.create(
            branch=branch,
            image="protected.jpg",
            alt_text="Protected",
        )

        self.client.force_authenticate(self.member_user)
        create_response = self.client.post(
            self.branch_images_url,
            data={
                "branch": branch.pk,
                "image": create_test_image_file("member-branch.gif"),
            },
            format="multipart",
        )
        self.assertEqual(create_response.status_code, status.HTTP_400_BAD_REQUEST)

        patch_response = self.client.patch(
            f"{self.branch_images_url}{image.pk}/",
            data={"alt_text": "Member edit"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_branch_image_branch_cannot_be_changed(self):
        first_branch = OrganizationBranch.objects.create(
            organization=self.organization,
            name="First Image Branch",
        )
        second_branch = OrganizationBranch.objects.create(
            organization=self.organization,
            name="Second Image Branch",
        )
        image = OrganizationBranchImage.objects.create(
            branch=first_branch,
            image="fixed-branch.jpg",
        )
        self.client.force_authenticate(self.manager)

        response = self.client.patch(
            f"{self.branch_images_url}{image.pk}/",
            data={"branch": second_branch.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        image.refresh_from_db()
        self.assertEqual(image.branch, first_branch)

    def test_manager_can_manage_event_images(self):
        event = Event.objects.create(
            title="Gallery Event",
            content="Created by manager",
            category=self.event_category,
            organization=self.organization,
            created_by_member=self.manager_membership,
            starts_at=timezone.now(),
        )
        self.client.force_authenticate(self.manager)

        create_response = self.client.post(
            self.event_images_url,
            data={
                "event": event.pk,
                "image": create_test_image_file(),
                "alt_text": "Start",
                "sort_order": 1,
            },
            format="multipart",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        image = EventImage.objects.get(pk=create_response.data["id"])

        patch_response = self.client.patch(
            f"{self.event_images_url}{image.pk}/",
            data={"alt_text": "Updated"},
            format="json",
        )
        delete_response = self.client.delete(f"{self.event_images_url}{image.pk}/")

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EventImage.objects.filter(pk=image.pk).exists())

    def test_manager_can_edit_and_delete_member_event_news(self):
        event = Event.objects.create(
            title="News Parent Event",
            content="Created by manager",
            category=self.event_category,
            organization=self.organization,
            created_by_member=self.manager_membership,
            starts_at=timezone.now(),
        )
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member_membership,
            title="Member News",
            text="Created by member",
            image="news.jpg",
        )
        self.client.force_authenticate(self.manager)

        patch_response = self.client.patch(
            f"{self.news_url}{news.pk}/",
            data={"title": "Manager Edited News"},
            format="json",
        )
        delete_response = self.client.delete(f"{self.news_url}{news.pk}/")

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OrganizationNews.objects.filter(pk=news.pk).exists())

    def test_organization_news_can_have_multiple_images(self):
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.manager_membership,
            title="Gallery News",
            text="News with several images",
        )

        first_image = OrganizationNewsImage.objects.create(
            news=news,
            image="first.jpg",
            alt_text="First image",
            sort_order=2,
        )
        second_image = OrganizationNewsImage.objects.create(
            news=news,
            image="second.jpg",
            alt_text="Second image",
            sort_order=1,
        )

        self.assertEqual(news.images.count(), 2)
        self.assertEqual(list(news.images.all()), [second_image, first_image])

    def test_news_images_api_respects_news_author_and_manager_permissions(self):
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member_membership,
            title="Member Gallery News",
            text="Created by member",
        )

        self.client.force_authenticate(self.outsider)
        outsider_response = self.client.post(
            self.news_images_url,
            data={
                "news": news.pk,
                "image": create_test_image_file("outsider.gif"),
                "alt_text": "Forbidden",
                "sort_order": 1,
            },
            format="multipart",
        )
        self.assertEqual(outsider_response.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(self.member_user)
        author_response = self.client.post(
            self.news_images_url,
            data={
                "news": news.pk,
                "image": create_test_image_file("author.gif"),
                "alt_text": "Author image",
                "sort_order": 1,
            },
            format="multipart",
        )
        self.assertEqual(author_response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.manager)
        manager_response = self.client.post(
            self.news_images_url,
            data={
                "news": news.pk,
                "image": create_test_image_file("manager.gif"),
                "alt_text": "Manager image",
                "sort_order": 2,
            },
            format="multipart",
        )
        self.assertEqual(manager_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(news.images.count(), 2)

    def test_only_news_author_or_manager_can_edit_news_image(self):
        news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.member_membership,
            title="Editable Gallery News",
            text="Created by member",
        )
        image = OrganizationNewsImage.objects.create(
            news=news,
            image="editable.jpg",
            alt_text="Initial",
        )

        self.client.force_authenticate(self.outsider)
        outsider_response = self.client.patch(
            f"{self.news_images_url}{image.pk}/",
            data={"alt_text": "Outsider edit"},
            format="json",
        )
        self.assertEqual(outsider_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.member_user)
        author_response = self.client.patch(
            f"{self.news_images_url}{image.pk}/",
            data={"alt_text": "Author edit"},
            format="json",
        )
        self.assertEqual(author_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.manager)
        manager_response = self.client.patch(
            f"{self.news_images_url}{image.pk}/",
            data={"alt_text": "Manager edit"},
            format="json",
        )
        self.assertEqual(manager_response.status_code, status.HTTP_200_OK)

    def test_news_image_news_cannot_be_changed(self):
        first_news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.manager_membership,
            title="First Gallery News",
            text="Text",
        )
        second_news = OrganizationNews.objects.create(
            organization=self.organization,
            created_by_member=self.manager_membership,
            title="Second Gallery News",
            text="Text",
        )
        image = OrganizationNewsImage.objects.create(
            news=first_news,
            image="fixed.jpg",
        )
        self.client.force_authenticate(self.manager)

        response = self.client.patch(
            f"{self.news_images_url}{image.pk}/",
            data={"news": second_news.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        image.refresh_from_db()
        self.assertEqual(image.news, first_news)


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
        self.admin_user = self.user_model.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="StrongPassword123!",
            is_staff=True,
            is_superuser=True,
        )

    def _payload(self, suffix="1"):
        return {
            "official_name": f"Фонд {suffix}",
            "legal_address": "г. Алматы, ул. Абая, 1",
            "phone": "+7 777 000 00 00",
            "email": f"fund{suffix}@example.com",
            "max_url": f"https://max.example.com/fund-{suffix}",
            "vk_url": f"https://vk.com/fund{suffix}",
            "website_url": f"https://fund{suffix}.example.com",
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

    def test_staff_user_without_superuser_cannot_approve_request(self):
        staff_user = self.user_model.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="StrongPassword123!",
            is_staff=True,
            is_superuser=False,
        )
        registration_request = self._create_request()
        self.client.force_authenticate(staff_user)

        response = self.client.post(f"{self.url}{registration_request.pk}/approve/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_without_staff_cannot_approve_request(self):
        superuser = self.user_model.objects.create_user(
            username="superuser",
            email="superuser@example.com",
            password="StrongPassword123!",
            is_staff=False,
            is_superuser=True,
        )
        registration_request = self._create_request()
        self.client.force_authenticate(superuser)

        response = self.client.post(f"{self.url}{registration_request.pk}/approve/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_superuser_sees_all_requests(self):
        self._create_request(user=self.user, suffix="3")
        self._create_request(user=self.other_user, suffix="4")
        self.client.force_authenticate(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_staff_superuser_can_approve_pending_request(self):
        registration_request = self._create_request()
        self.client.force_authenticate(self.admin_user)

        response = self.client.post(f"{self.url}{registration_request.pk}/approve/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        registration_request.refresh_from_db()
        organization = Organization.objects.get(pk=registration_request.organization_id)
        membership = OrganizationMember.objects.get(
            organization=organization,
            user=self.user,
        )
        self.assertEqual(registration_request.status, OrganizationRegistrationRequest.Status.APPROVED)
        self.assertEqual(registration_request.reviewed_by, self.admin_user)
        self.assertEqual(organization.created_by, self.user)
        self.assertEqual(organization.official_name, registration_request.official_name)
        self.assertEqual(organization.max_url, registration_request.max_url)
        self.assertEqual(organization.vk_url, registration_request.vk_url)
        self.assertEqual(organization.website_url, registration_request.website_url)
        self.assertEqual(membership.role, OrganizationMember.Role.MANAGER)

    def test_staff_superuser_can_reject_pending_request(self):
        registration_request = self._create_request(suffix="5")
        self.client.force_authenticate(self.admin_user)

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
        self.client.force_authenticate(self.admin_user)

        response = self.client.post(f"{self.url}{registration_request.pk}/approve/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_reject_approved_request(self):
        registration_request = self._create_request(suffix="7")
        registration_request.status = OrganizationRegistrationRequest.Status.APPROVED
        registration_request.save(update_fields=("status", "updated_at"))
        self.client.force_authenticate(self.admin_user)

        response = self.client.post(
            f"{self.url}{registration_request.pk}/reject/",
            data={"rejection_reason": "Поздно"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

