from rest_framework import serializers
from django.db.models import Sum

from apps.accounts.models import CourierProfile
from apps.organizations.models import OrganizationMember
from apps.organizations.permissions import is_active_organization_manager

from .models import (
    BranchItem,
    Collection,
    CollectionItem,
    DonorGroup,
    DonorGroupItem,
    DonorGroupParameters,
    DonorGroupMember,
    DonorGroupVideoReport,
    ItemCategory,
    MeetingPlaceProposal,
    Poll,
    PollOption,
    PollVote,
    UserItem,
)
from .permissions import (
    is_donor_group_member,
    is_collection_author_or_manager,
    is_donor_group_collection_author_or_manager,
    is_poll_manager,
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
    selected_quantity = serializers.SerializerMethodField()
    available_quantity = serializers.SerializerMethodField()

    class Meta:
        model = UserItem
        fields = (
            "id",
            "user",
            "user_email",
            "category",
            "category_name",
            "quantity",
            "selected_quantity",
            "available_quantity",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "user_email",
            "category_name",
            "selected_quantity",
            "available_quantity",
            "created_at",
            "updated_at",
        )

    def get_selected_quantity(self, obj):
        queryset = obj.donor_group_items.all()
        request = self.context.get("request")
        collection_id = getattr(request, "query_params", {}).get("collection") if request else None
        if collection_id:
            queryset = queryset.filter(donor_group__collection_id=collection_id)
        return queryset.aggregate(total=Sum("quantity"))["total"] or 0

    def get_available_quantity(self, obj):
        return max(obj.quantity - self.get_selected_quantity(obj), 0)


class CollectionItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    selected_quantity = serializers.SerializerMethodField()
    remaining_quantity = serializers.SerializerMethodField()

    class Meta:
        model = CollectionItem
        fields = (
            "id",
            "collection",
            "category",
            "category_name",
            "quantity_required",
            "selected_quantity",
            "remaining_quantity",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "category_name",
            "selected_quantity",
            "remaining_quantity",
            "created_at",
            "updated_at",
        )

    def get_selected_quantity(self, obj):
        return DonorGroupItem.objects.filter(
            donor_group__collection=obj.collection,
            user_item__category=obj.category,
        ).aggregate(total=Sum("quantity"))["total"] or 0

    def get_remaining_quantity(self, obj):
        if obj.quantity_required is None:
            return None
        return max(obj.quantity_required - self.get_selected_quantity(obj), 0)

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
    quantity_required_total = serializers.SerializerMethodField()
    quantity_selected_total = serializers.SerializerMethodField()
    donor_groups_count = serializers.SerializerMethodField()
    donor_group_members_count = serializers.SerializerMethodField()
    donor_group_items_count = serializers.SerializerMethodField()

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
            "quantity_required_total",
            "quantity_selected_total",
            "donor_groups_count",
            "donor_group_members_count",
            "donor_group_items_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "organization_name",
            "created_by_member",
            "items",
            "items_count",
            "quantity_required_total",
            "quantity_selected_total",
            "donor_groups_count",
            "donor_group_members_count",
            "donor_group_items_count",
            "created_at",
            "updated_at",
        )

    def get_items_count(self, obj):
        return obj.items.count()

    def get_quantity_required_total(self, obj):
        return obj.items.aggregate(total=Sum("quantity_required"))["total"] or 0

    def get_quantity_selected_total(self, obj):
        return DonorGroupItem.objects.filter(
            donor_group__collection=obj,
        ).aggregate(total=Sum("quantity"))["total"] or 0

    def get_donor_groups_count(self, obj):
        return obj.donor_groups.count()

    def get_donor_group_members_count(self, obj):
        return DonorGroupMember.objects.filter(donor_group__collection=obj).count()

    def get_donor_group_items_count(self, obj):
        return DonorGroupItem.objects.filter(donor_group__collection=obj).count()

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


class DonorGroupParametersSerializer(serializers.ModelSerializer):
    finalized_by_member = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DonorGroupParameters
        fields = (
            "id",
            "donor_group",
            "geodata",
            "street",
            "description",
            "starts_at",
            "ends_at",
            "finalized_by_member",
            "finalized_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "donor_group",
            "finalized_by_member",
            "finalized_at",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        geodata = attrs.get("geodata", getattr(self.instance, "geodata", None))
        street = attrs.get("street", getattr(self.instance, "street", ""))
        description = attrs.get("description", getattr(self.instance, "description", ""))
        if not (geodata or street or description):
            raise serializers.ValidationError(
                {"geodata": "Parameters require place data."}
            )

        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at is None:
            raise serializers.ValidationError({"starts_at": "Parameters require starts_at."})
        if ends_at and ends_at < starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End date cannot be earlier than start date."}
            )
        return attrs


class DonorGroupParametersTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorGroupParameters
        fields = (
            "starts_at",
            "ends_at",
        )

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at is None:
            raise serializers.ValidationError({"starts_at": "Parameters require starts_at."})
        if ends_at and ends_at < starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End date cannot be earlier than start date."}
            )
        return attrs


class DonorGroupSerializer(serializers.ModelSerializer):
    created_by_member = serializers.PrimaryKeyRelatedField(read_only=True)
    members = DonorGroupMemberSerializer(many=True, read_only=True)
    items = DonorGroupItemSerializer(many=True, read_only=True)
    parameters = DonorGroupParametersSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    video_reports_count = serializers.SerializerMethodField()

    class Meta:
        model = DonorGroup
        fields = (
            "id",
            "collection",
            "created_by_member",
            "title",
            "members",
            "items",
            "parameters",
            "members_count",
            "items_count",
            "video_reports_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by_member",
            "members",
            "items",
            "parameters",
            "members_count",
            "items_count",
            "video_reports_count",
            "created_at",
            "updated_at",
        )

    def get_members_count(self, obj):
        return obj.members.count()

    def get_items_count(self, obj):
        return obj.items.count()

    def get_video_reports_count(self, obj):
        return obj.video_reports.count()

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


class MeetingPlaceProposalSerializer(serializers.ModelSerializer):
    proposed_by_email = serializers.EmailField(source="proposed_by.email", read_only=True)

    class Meta:
        model = MeetingPlaceProposal
        fields = (
            "id",
            "donor_group",
            "proposed_by",
            "proposed_by_email",
            "geodata",
            "street",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "proposed_by", "proposed_by_email", "created_at", "updated_at")

    def validate_donor_group(self, donor_group):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_donor_group_member(donor_group=donor_group, user=user):
            raise serializers.ValidationError("Only donor group members can propose meeting places.")
        return donor_group

    def validate(self, attrs):
        if self.instance and "donor_group" in attrs and attrs["donor_group"] != self.instance.donor_group:
            raise serializers.ValidationError({"donor_group": "Donor group cannot be changed."})
        geodata = attrs.get("geodata", getattr(self.instance, "geodata", None))
        street = attrs.get("street", getattr(self.instance, "street", ""))
        description = attrs.get("description", getattr(self.instance, "description", ""))
        if not (geodata or street or description):
            raise serializers.ValidationError(
                {"geodata": "Meeting place proposal requires place data."}
            )
        return attrs


class PollOptionSerializer(serializers.ModelSerializer):
    votes_count = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = (
            "id",
            "poll",
            "text",
            "starts_at",
            "ends_at",
            "geodata",
            "place_street",
            "place_description",
            "source_place_proposal",
            "sort_order",
            "votes_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "votes_count", "created_at", "updated_at")

    def get_votes_count(self, obj):
        votes_count = getattr(obj, "votes_count", None)
        if votes_count is not None:
            return votes_count
        return obj.votes.count()

    def validate_poll(self, poll):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_poll_manager(poll=poll, user=user):
            raise serializers.ValidationError("Only the poll organizer or manager can manage options.")
        return poll

    def validate(self, attrs):
        if self.instance and "poll" in attrs and attrs["poll"] != self.instance.poll:
            raise serializers.ValidationError({"poll": "Poll cannot be changed."})
        poll = attrs.get("poll", getattr(self.instance, "poll", None))
        source_place_proposal = attrs.get(
            "source_place_proposal",
            getattr(self.instance, "source_place_proposal", None),
        )
        if (
            poll
            and source_place_proposal
            and poll.donor_group_id != source_place_proposal.donor_group_id
        ):
            raise serializers.ValidationError(
                {"source_place_proposal": "Proposal must belong to the poll donor group."}
            )
        if poll:
            self._validate_by_kind(poll=poll, attrs=attrs)
        return attrs

    def _validate_by_kind(self, *, poll, attrs):
        text = attrs.get("text", getattr(self.instance, "text", ""))
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        geodata = attrs.get("geodata", getattr(self.instance, "geodata", None))
        place_street = attrs.get("place_street", getattr(self.instance, "place_street", ""))
        place_description = attrs.get(
            "place_description",
            getattr(self.instance, "place_description", ""),
        )
        if poll.kind == Poll.Kind.TEXT and not text:
            raise serializers.ValidationError({"text": "Text option requires text."})
        if poll.kind == Poll.Kind.DATE and not starts_at:
            raise serializers.ValidationError({"starts_at": "Date option requires starts_at."})
        if starts_at and ends_at and ends_at < starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End date cannot be earlier than start date."}
            )
        if poll.kind == Poll.Kind.PLACE and not (geodata or place_street or place_description):
            raise serializers.ValidationError({"geodata": "Place option requires place data."})


class PollSerializer(serializers.ModelSerializer):
    created_by_member = serializers.PrimaryKeyRelatedField(read_only=True)
    options = PollOptionSerializer(many=True, read_only=True)
    options_count = serializers.SerializerMethodField()
    votes_count = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = (
            "id",
            "donor_group",
            "news",
            "created_by_member",
            "source_poll",
            "finalized_option",
            "finalized_by_member",
            "finalized_at",
            "title",
            "description",
            "kind",
            "status",
            "closes_at",
            "options",
            "options_count",
            "votes_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by_member",
            "source_poll",
            "finalized_option",
            "finalized_by_member",
            "finalized_at",
            "options",
            "options_count",
            "votes_count",
            "created_at",
            "updated_at",
        )

    def get_options_count(self, obj):
        return obj.options.count()

    def get_votes_count(self, obj):
        return obj.votes.count()

    def validate(self, attrs):
        if self.instance:
            if "donor_group" in attrs and attrs["donor_group"] != self.instance.donor_group:
                raise serializers.ValidationError({"donor_group": "Donor group cannot be changed."})
            if "news" in attrs and attrs["news"] != self.instance.news:
                raise serializers.ValidationError({"news": "News cannot be changed."})

        donor_group = attrs.get("donor_group", getattr(self.instance, "donor_group", None))
        news = attrs.get("news", getattr(self.instance, "news", None))
        if not donor_group and not news:
            raise serializers.ValidationError("Poll must be attached to a donor group or news.")
        if donor_group and news and donor_group.collection.organization_id != news.organization_id:
            raise serializers.ValidationError(
                {"news": "News must belong to the donor group collection organization."}
            )

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if donor_group and not is_donor_group_collection_author_or_manager(
            donor_group=donor_group,
            user=user,
        ):
            raise serializers.ValidationError(
                "Only the collection author or manager can manage donor group polls."
            )
        if news and not (
            news.created_by_member.user_id == getattr(user, "id", None)
            and news.created_by_member.is_active
        ) and not is_active_organization_manager(organization=news.organization, user=user):
            raise serializers.ValidationError(
                "Only the news author or organization manager can manage news polls."
            )
        return attrs


class PollVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollVote
        fields = (
            "id",
            "poll",
            "option",
            "user",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def validate(self, attrs):
        if self.instance and "poll" in attrs and attrs["poll"] != self.instance.poll:
            raise serializers.ValidationError({"poll": "Poll cannot be changed."})
        poll = attrs.get("poll", getattr(self.instance, "poll", None))
        option = attrs.get("option", getattr(self.instance, "option", None))
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if poll and poll.status != Poll.Status.OPEN:
            raise serializers.ValidationError({"poll": "Only open polls accept votes."})
        if poll and option and option.poll_id != poll.id:
            raise serializers.ValidationError({"option": "Option must belong to the selected poll."})
        if poll and poll.donor_group_id and not is_donor_group_member(
            donor_group=poll.donor_group,
            user=user,
        ):
            raise serializers.ValidationError(
                "Only donor group members can vote in donor group polls."
            )
        if poll and user and not self.instance and PollVote.objects.filter(
            poll=poll,
            user=user,
        ).exists():
            raise serializers.ValidationError({"poll": "User has already voted in this poll."})
        return attrs


class PollRepostSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Poll.Status.choices, default=Poll.Status.OPEN)
    closes_at = serializers.DateTimeField(required=False, allow_null=True)


class PollFinalizeSerializer(serializers.Serializer):
    option = serializers.PrimaryKeyRelatedField(queryset=PollOption.objects.all())

    def validate_option(self, option):
        poll = self.context["poll"]
        if option.poll_id != poll.id:
            raise serializers.ValidationError("Option must belong to this poll.")
        return option

    def validate(self, attrs):
        poll = self.context["poll"]
        if not poll.donor_group_id:
            raise serializers.ValidationError("Only donor group polls can finalize parameters.")
        if poll.kind not in (Poll.Kind.DATE, Poll.Kind.PLACE):
            raise serializers.ValidationError("Only date and place polls can finalize parameters.")
        return attrs


class PlaceProposalPollCreateSerializer(serializers.Serializer):
    donor_group = serializers.PrimaryKeyRelatedField(queryset=DonorGroup.objects.all())
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Poll.Status.choices, default=Poll.Status.OPEN)
    closes_at = serializers.DateTimeField(required=False, allow_null=True)
    proposal_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
    )

    def validate_donor_group(self, donor_group):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_donor_group_collection_author_or_manager(
            donor_group=donor_group,
            user=user,
        ):
            raise serializers.ValidationError(
                "Only the collection author or manager can create proposal polls."
            )
        return donor_group


class DonorGroupVideoReportSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True)

    class Meta:
        model = DonorGroupVideoReport
        fields = (
            "id",
            "donor_group",
            "uploaded_by",
            "uploaded_by_email",
            "title",
            "description",
            "video",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        )

    def validate_donor_group(self, donor_group):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not is_donor_group_member(donor_group=donor_group, user=user):
            raise serializers.ValidationError("Only donor group members can upload video reports.")
        return donor_group

    def validate(self, attrs):
        if self.instance and "donor_group" in attrs and attrs["donor_group"] != self.instance.donor_group:
            raise serializers.ValidationError({"donor_group": "Donor group cannot be changed."})
        return attrs
