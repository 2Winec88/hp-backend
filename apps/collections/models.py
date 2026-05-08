from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class ItemCategory(models.Model):
    class Unit(models.TextChoices):
        PIECE = "piece", "Штуки"
        PACK = "pack", "Упаковки"
        BOX = "box", "Коробки"
        KG = "kg", "Килограммы"
        LITER = "liter", "Литры"

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
        default=Unit.PIECE,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item category"
        verbose_name_plural = "Item categories"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Item(models.Model):
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("category", "name"),
                name="unique_item_name_per_category",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class UserItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_items",
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name="user_items",
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User item"
        verbose_name_plural = "User items"
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"{self.user} - {self.category.name} x{self.quantity}"


class Collection(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="collections",
    )
    created_by_member = models.ForeignKey(
        "organizations.OrganizationMember",
        on_delete=models.CASCADE,
        related_name="created_collections",
    )
    branch = models.ForeignKey(
        "organizations.OrganizationBranch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collections",
    )
    geodata = models.ForeignKey(
        "common.GeoData",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collections",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        ordering = ("-created_at", "-id")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if (
            self.created_by_member_id
            and self.organization_id
            and self.created_by_member.organization_id != self.organization_id
        ):
            raise ValidationError(
                {"created_by_member": "Creator must be a member of this organization."}
            )
        if (
            self.branch_id
            and self.organization_id
            and self.branch.organization_id != self.organization_id
        ):
            raise ValidationError(
                {"branch": "Branch must belong to the collection organization."}
            )
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError(
                {"ends_at": "End date cannot be earlier than start date."}
            )


class CollectionItem(models.Model):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name="collection_items",
    )
    quantity_required = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Collection item"
        verbose_name_plural = "Collection items"
        ordering = ("collection", "category__name", "id")

    def __str__(self):
        quantity = f" x{self.quantity_required}" if self.quantity_required else ""
        return f"{self.collection} - {self.category.name}{quantity}"


class BranchItem(models.Model):
    branch = models.ForeignKey(
        "organizations.OrganizationBranch",
        on_delete=models.CASCADE,
        related_name="accepted_items",
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name="branch_items",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Branch item"
        verbose_name_plural = "Branch items"
        ordering = ("branch", "category__name", "id")

    def __str__(self):
        return f"{self.branch} - {self.category.name}"


class DonorGroup(models.Model):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="donor_groups",
    )
    created_by_member = models.ForeignKey(
        "organizations.OrganizationMember",
        on_delete=models.CASCADE,
        related_name="created_donor_groups",
    )
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Donor group"
        verbose_name_plural = "Donor groups"
        ordering = ("-created_at", "-id")

    def __str__(self):
        return self.title or f"Donor group #{self.pk}"

    def clean(self):
        super().clean()
        if (
            self.created_by_member_id
            and self.collection_id
            and self.created_by_member.organization_id != self.collection.organization_id
        ):
            raise ValidationError(
                {"created_by_member": "Creator must be a member of the collection organization."}
            )


class DonorGroupMember(models.Model):
    donor_group = models.ForeignKey(
        DonorGroup,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donor_group_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Donor group member"
        verbose_name_plural = "Donor group members"
        ordering = ("donor_group", "joined_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("donor_group", "user"),
                name="unique_donor_group_member",
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.donor_group}"


class DonorGroupItem(models.Model):
    donor_group = models.ForeignKey(
        DonorGroup,
        on_delete=models.CASCADE,
        related_name="items",
    )
    user_item = models.ForeignKey(
        UserItem,
        on_delete=models.PROTECT,
        related_name="donor_group_items",
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Donor group item"
        verbose_name_plural = "Donor group items"
        ordering = ("donor_group", "user_item", "id")

    def __str__(self):
        return f"{self.donor_group} - {self.user_item} x{self.quantity}"

    def clean(self):
        super().clean()
        if self.user_item_id and self.quantity > self.user_item.quantity:
            raise ValidationError(
                {"quantity": "Selected quantity cannot exceed the user's item quantity."}
            )
        if (
            self.donor_group_id
            and self.user_item_id
            and not DonorGroupMember.objects.filter(
                donor_group=self.donor_group,
                user=self.user_item.user,
            ).exists()
        ):
            raise ValidationError(
                {"user_item": "The user item owner must be a donor group member."}
            )


class CourierProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courier_profile",
    )
    car_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Courier profile"
        verbose_name_plural = "Courier profiles"
        ordering = ("user__email", "id")

    def __str__(self):
        return f"{self.user} - {self.car_name}"
