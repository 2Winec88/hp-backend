from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


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


class DonorGroupMeeting(models.Model):
    donor_group = models.OneToOneField(
        DonorGroup,
        on_delete=models.CASCADE,
        related_name="meeting",
    )
    geodata = models.ForeignKey(
        "common.GeoData",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donor_group_meetings",
    )
    street = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    finalized_by_member = models.ForeignKey(
        "organizations.OrganizationMember",
        on_delete=models.PROTECT,
        related_name="finalized_donor_group_meetings",
    )
    finalized_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Donor group meeting"
        verbose_name_plural = "Donor group meetings"
        ordering = ("-finalized_at", "-id")

    def __str__(self):
        return f"{self.donor_group} meeting at {self.starts_at}"

    def clean(self):
        super().clean()
        if self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError({"ends_at": "End date cannot be earlier than start date."})
        if not (self.geodata_id or self.street or self.description):
            raise ValidationError({"geodata": "Meeting requires place data."})


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


class Poll(models.Model):
    class Kind(models.TextChoices):
        TEXT = "text", "Text"
        DATE = "date", "Date"
        PLACE = "place", "Place"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    donor_group = models.ForeignKey(
        DonorGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="polls",
    )
    news = models.ForeignKey(
        "organizations.OrganizationNews",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="polls",
    )
    created_by_member = models.ForeignKey(
        "organizations.OrganizationMember",
        on_delete=models.CASCADE,
        related_name="created_polls",
    )
    source_poll = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reposted_polls",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.TEXT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    closes_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Poll"
        verbose_name_plural = "Polls"
        ordering = ("-created_at", "-id")

    def __str__(self):
        return self.title

    @property
    def organization(self):
        if self.donor_group_id:
            return self.donor_group.collection.organization
        if self.news_id:
            return self.news.organization
        return None

    def clean(self):
        super().clean()
        if not self.donor_group_id and not self.news_id:
            raise ValidationError("Poll must be attached to a donor group or news.")
        if self.donor_group_id and self.news_id:
            donor_group_org_id = self.donor_group.collection.organization_id
            if self.news.organization_id != donor_group_org_id:
                raise ValidationError(
                    {"news": "News must belong to the donor group collection organization."}
                )
        organization = self.organization
        if (
            self.created_by_member_id
            and organization
            and self.created_by_member.organization_id != organization.id
        ):
            raise ValidationError(
                {"created_by_member": "Creator must be a member of the poll organization."}
            )


class MeetingPlaceProposal(models.Model):
    donor_group = models.ForeignKey(
        DonorGroup,
        on_delete=models.CASCADE,
        related_name="place_proposals",
    )
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meeting_place_proposals",
    )
    geodata = models.ForeignKey(
        "common.GeoData",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meeting_place_proposals",
    )
    street = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Meeting place proposal"
        verbose_name_plural = "Meeting place proposals"
        ordering = ("donor_group", "-created_at", "-id")

    def __str__(self):
        return f"{self.donor_group} - {self.street or self.geodata_id or self.pk}"


class PollOption(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=255, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    geodata = models.ForeignKey(
        "common.GeoData",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="poll_options",
    )
    place_street = models.CharField(max_length=255, blank=True)
    place_description = models.TextField(blank=True)
    source_place_proposal = models.ForeignKey(
        MeetingPlaceProposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="poll_options",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Poll option"
        verbose_name_plural = "Poll options"
        ordering = ("poll", "sort_order", "id")

    def __str__(self):
        return self.text or self.place_street or f"Poll option #{self.pk}"

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError({"ends_at": "End date cannot be earlier than start date."})
        if self.poll_id:
            if self.poll.kind == Poll.Kind.TEXT and not self.text:
                raise ValidationError({"text": "Text option requires text."})
            if self.poll.kind == Poll.Kind.DATE and not self.starts_at:
                raise ValidationError({"starts_at": "Date option requires starts_at."})
            if self.poll.kind == Poll.Kind.PLACE and not (
                self.geodata_id or self.place_street or self.place_description
            ):
                raise ValidationError({"geodata": "Place option requires place data."})


class PollVote(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    option = models.ForeignKey(
        PollOption,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="poll_votes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Poll vote"
        verbose_name_plural = "Poll votes"
        ordering = ("poll", "created_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("poll", "user"),
                name="unique_poll_vote_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.option}"

    def clean(self):
        super().clean()
        if self.option_id and self.poll_id and self.option.poll_id != self.poll_id:
            raise ValidationError({"option": "Option must belong to the selected poll."})
