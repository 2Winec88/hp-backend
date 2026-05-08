from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.organizations.models import (
    Organization,
    OrganizationBranch,
    OrganizationMember,
)

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


class ItemCategorySeedTests(TestCase):
    def test_humanitarian_item_categories_are_seeded(self):
        expected_categories = {
            "Зубная гигиена": "зубная паста, зубные щётки",
            "Мыло и базовая гигиена": "мыло, шампунь, влажные салфетки",
            "Питьевая вода": "бутылки воды, канистры, вода 5 л",
            "Крупы и макароны": "рис, гречка, макароны",
            "Мясные консервы": "тушёнка, паштеты, рыбные консервы",
            "Постельное бельё": "простыни, наволочки, пододеяльники",
            "Батарейки и аккумуляторы": "AA, AAA, аккумуляторные элементы",
            "Одеяла и пледы": "одеяла, флисовые пледы",
            "Зарядные устройства": "зарядки для телефонов, кабели, автомобильные зарядки",
            "Футболки и кофты": "футболки, толстовки, свитеры",
            "Фонарики": "ручные фонари, налобные фонари",
            "Брюки": "спортивные штаны, брюки, джинсы",
            "Спальные мешки": "летние и утеплённые спальники",
            "Обувь": "ботинки, сапоги, кроссовки",
            "Куртки": "демисезонные и зимние куртки",
            "Электрообогреватели": "масляные, конвекторные обогреватели",
            "Генераторы": "бензиновые генераторы",
        }

        categories = {
            category.name: category.description
            for category in ItemCategory.objects.filter(name__in=expected_categories)
        }

        self.assertEqual(categories, expected_categories)


class CollectionPermissionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.manager = user_model.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="password",
        )
        self.member = user_model.objects.create_user(
            username="member",
            email="member@example.com",
            password="password",
        )
        self.other = user_model.objects.create_user(
            username="other",
            email="other@example.com",
            password="password",
        )
        self.donor = user_model.objects.create_user(
            username="donor",
            email="donor@example.com",
            password="password",
        )
        self.organization = Organization.objects.create(
            official_name="Help Org",
            legal_address="Main street",
            phone="+70000000000",
            email="org@example.com",
            executive_person_full_name="Director",
            executive_authority_basis="Charter",
            executive_body_name="Board",
            created_by=self.manager,
        )
        self.other_organization = Organization.objects.create(
            official_name="Other Org",
            legal_address="Other street",
            phone="+71111111111",
            email="other-org@example.com",
            executive_person_full_name="Other Director",
            executive_authority_basis="Charter",
            executive_body_name="Board",
            created_by=self.other,
        )
        self.manager_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.manager,
            role=OrganizationMember.Role.MANAGER,
        )
        self.member_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.member,
            role=OrganizationMember.Role.MEMBER,
        )
        self.other_membership = OrganizationMember.objects.create(
            organization=self.other_organization,
            user=self.other,
            role=OrganizationMember.Role.MANAGER,
        )
        self.branch = OrganizationBranch.objects.create(
            organization=self.organization,
            name="Main branch",
        )
        self.other_branch = OrganizationBranch.objects.create(
            organization=self.other_organization,
            name="Other branch",
        )
        self.category = ItemCategory.objects.create(name="Water")
        self.client = APIClient()

    def test_user_items_are_public_but_only_owner_can_edit(self):
        user_item = UserItem.objects.create(
            user=self.donor,
            category=self.category,
            quantity=2,
        )

        response = self.client.get(reverse("user-item-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse("user-item-list"),
            {"category": self.category.id, "quantity": 3},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], self.member.id)

        response = self.client.patch(
            reverse("user-item-detail", args=(user_item.id,)),
            {"quantity": 5},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.donor)
        response = self.client.patch(
            reverse("user-item-detail", args=(user_item.id,)),
            {"quantity": 4},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_item.refresh_from_db()
        self.assertEqual(user_item.quantity, 4)

    def test_collection_create_requires_active_organization_member(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse("collection-list"),
            {
                "organization": self.organization.id,
                "branch": self.branch.id,
                "title": "Winter help",
                "description": "Warm clothes",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        collection = Collection.objects.get(pk=response.data["id"])
        self.assertEqual(collection.created_by_member, self.member_membership)

        self.client.force_authenticate(user=self.donor)
        response = self.client.post(
            reverse("collection-list"),
            {
                "organization": self.organization.id,
                "title": "Bad create",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_collection_is_public_but_only_author_or_manager_can_edit(self):
        collection = Collection.objects.create(
            organization=self.organization,
            created_by_member=self.member_membership,
            title="Food",
        )

        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("collection-detail", args=(collection.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.donor)
        response = self.client.patch(
            reverse("collection-detail", args=(collection.id,)),
            {"title": "Nope"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.member)
        response = self.client.patch(
            reverse("collection-detail", args=(collection.id,)),
            {"title": "Food updated"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            reverse("collection-detail", args=(collection.id,)),
            {"status": Collection.Status.PUBLISHED},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_collection_rejects_branch_from_another_organization(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse("collection-list"),
            {
                "organization": self.organization.id,
                "branch": self.other_branch.id,
                "title": "Wrong branch",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("branch", response.data)

    def test_collection_items_follow_collection_author_and_manager_permissions(self):
        collection = Collection.objects.create(
            organization=self.organization,
            created_by_member=self.member_membership,
            title="Food",
        )
        collection_item = CollectionItem.objects.create(
            collection=collection,
            category=self.category,
            quantity_required=10,
        )

        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("collection-item-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.donor)
        response = self.client.patch(
            reverse("collection-item-detail", args=(collection_item.id,)),
            {"quantity_required": 11},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse("collection-item-list"),
            {
                "collection": collection.id,
                "category": self.category.id,
                "quantity_required": 5,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            reverse("collection-item-detail", args=(collection_item.id,)),
            {"description": "Manager update"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_branch_items_are_public_but_only_organization_manager_can_write(self):
        branch_item = BranchItem.objects.create(
            branch=self.branch,
            category=self.category,
        )

        response = self.client.get(reverse("branch-item-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse("branch-item-list"),
            {
                "branch": self.branch.id,
                "category": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.patch(
            reverse("branch-item-detail", args=(branch_item.id,)),
            {"description": "Member update"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            reverse("branch-item-list"),
            {
                "branch": self.branch.id,
                "category": self.category.id,
                "description": "Accepted here",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.delete(reverse("branch-item-detail", args=(branch_item.id,)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_donor_groups_are_managed_by_collection_author_or_manager(self):
        collection = Collection.objects.create(
            organization=self.organization,
            created_by_member=self.member_membership,
            title="Food",
        )
        donor_group = DonorGroup.objects.create(
            collection=collection,
            created_by_member=self.member_membership,
            title="First group",
        )

        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("donor-group-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.donor)
        response = self.client.patch(
            reverse("donor-group-detail", args=(donor_group.id,)),
            {"title": "Nope"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse("donor-group-list"),
            {
                "collection": collection.id,
                "title": "Author group",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_group = DonorGroup.objects.get(pk=response.data["id"])
        self.assertEqual(created_group.created_by_member, self.member_membership)

        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            reverse("donor-group-detail", args=(donor_group.id,)),
            {"title": "Manager update"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_donor_group_members_and_items_are_managed_by_collection_author_or_manager(self):
        collection = Collection.objects.create(
            organization=self.organization,
            created_by_member=self.member_membership,
            title="Food",
        )
        donor_group = DonorGroup.objects.create(
            collection=collection,
            created_by_member=self.member_membership,
        )
        donor_group_member = DonorGroupMember.objects.create(
            donor_group=donor_group,
            user=self.donor,
        )
        user_item = UserItem.objects.create(
            user=self.donor,
            category=self.category,
            quantity=3,
        )
        donor_group_item = DonorGroupItem.objects.create(
            donor_group=donor_group,
            user_item=user_item,
            quantity=2,
        )

        self.client.force_authenticate(user=self.donor)
        response = self.client.patch(
            reverse("donor-group-member-detail", args=(donor_group_member.id,)),
            {"user": self.other.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(
            reverse("donor-group-item-detail", args=(donor_group_item.id,)),
            {"quantity": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse("donor-group-member-list"),
            {
                "donor_group": donor_group.id,
                "user": self.other.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            reverse("donor-group-item-list"),
            {
                "donor_group": donor_group.id,
                "user_item": user_item.id,
                "quantity": 4,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            reverse("donor-group-member-detail", args=(donor_group_member.id,)),
            {"user": self.other.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.patch(
            reverse("donor-group-item-detail", args=(donor_group_item.id,)),
            {"quantity": 3},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_courier_profiles_are_public_but_only_owner_can_edit(self):
        courier_profile = CourierProfile.objects.create(
            user=self.donor,
            car_name="Lada Granta",
        )

        response = self.client.get(reverse("courier-profile-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse("courier-profile-list"),
            {"car_name": "Gazelle"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], self.member.id)

        response = self.client.patch(
            reverse("courier-profile-detail", args=(courier_profile.id,)),
            {"car_name": "Not mine"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.donor)
        response = self.client.post(
            reverse("courier-profile-list"),
            {"car_name": "Duplicate"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.patch(
            reverse("courier-profile-detail", args=(courier_profile.id,)),
            {"car_name": "Lada Largus"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        courier_profile.refresh_from_db()
        self.assertEqual(courier_profile.car_name, "Lada Largus")
