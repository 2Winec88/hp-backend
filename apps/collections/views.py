from django.db import transaction
from django.db.models import Count
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.organizations.models import OrganizationMember
from apps.communications.services import create_notification

from .models import (
    BranchItem,
    Collection,
    CollectionItem,
    CourierProfile,
    DonorGroup,
    DonorGroupItem,
    DonorGroupMember,
    ItemCategory,
    MeetingPlaceProposal,
    Poll,
    PollOption,
    PollVote,
    UserItem,
)
from .permissions import (
    IsReadOnlyOrBranchItemOrganizationManager,
    IsReadOnlyOrCollectionAuthorOrOrganizationManager,
    IsReadOnlyOrCollectionItemAuthorOrOrganizationManager,
    IsReadOnlyOrCourierProfileOwner,
    IsReadOnlyOrDonorGroupCollectionAuthorOrOrganizationManager,
    IsReadOnlyOrDonorGroupItemManager,
    IsReadOnlyOrDonorGroupMemberManager,
    IsReadOnlyOrMeetingPlaceProposalOwnerOrGroupManager,
    IsReadOnlyOrPollManager,
    IsReadOnlyOrPollOptionManager,
    IsPollVoteOwner,
    IsReadOnlyOrUserItemOwner,
)
from .serializers import (
    BranchItemSerializer,
    CollectionItemSerializer,
    CollectionSerializer,
    CourierProfileSerializer,
    DonorGroupItemSerializer,
    DonorGroupMemberSerializer,
    DonorGroupSerializer,
    ItemCategorySerializer,
    MeetingPlaceProposalSerializer,
    PlaceProposalPollCreateSerializer,
    PollOptionSerializer,
    PollRepostSerializer,
    PollSerializer,
    PollVoteSerializer,
    UserItemSerializer,
)


class ItemCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        queryset = ItemCategory.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ("1", "true", "yes"))
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class UserItemViewSet(viewsets.ModelViewSet):
    serializer_class = UserItemSerializer
    permission_classes = [IsReadOnlyOrUserItemOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = UserItem.objects.select_related("user", "category")
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(category__name__icontains=search)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [IsReadOnlyOrCollectionAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = Collection.objects.select_related(
            "organization",
            "created_by_member",
            "created_by_member__user",
            "branch",
            "geodata",
            "geodata__city",
            "geodata__city__region",
        ).prefetch_related("items", "items__category")

        organization_id = self.request.query_params.get("organization")
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        organization = serializer.validated_data["organization"]
        member = OrganizationMember.objects.get(
            organization=organization,
            user=self.request.user,
            is_active=True,
        )
        serializer.save(created_by_member=member)


class CollectionItemViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionItemSerializer
    permission_classes = [IsReadOnlyOrCollectionItemAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = CollectionItem.objects.select_related(
            "collection",
            "collection__organization",
            "collection__created_by_member",
            "collection__created_by_member__user",
            "category",
        )
        collection_id = self.request.query_params.get("collection")
        if collection_id:
            queryset = queryset.filter(collection_id=collection_id)
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class BranchItemViewSet(viewsets.ModelViewSet):
    serializer_class = BranchItemSerializer
    permission_classes = [IsReadOnlyOrBranchItemOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = BranchItem.objects.select_related(
            "branch",
            "branch__organization",
            "category",
        )
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class DonorGroupViewSet(viewsets.ModelViewSet):
    serializer_class = DonorGroupSerializer
    permission_classes = [IsReadOnlyOrDonorGroupCollectionAuthorOrOrganizationManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = DonorGroup.objects.select_related(
            "collection",
            "collection__organization",
            "collection__created_by_member",
            "collection__created_by_member__user",
            "created_by_member",
            "created_by_member__user",
        ).prefetch_related(
            "members",
            "members__user",
            "items",
            "items__user_item",
            "items__user_item__user",
            "items__user_item__category",
        )
        collection_id = self.request.query_params.get("collection")
        if collection_id:
            queryset = queryset.filter(collection_id=collection_id)
        return queryset

    def perform_create(self, serializer):
        collection = serializer.validated_data["collection"]
        member = OrganizationMember.objects.get(
            organization=collection.organization,
            user=self.request.user,
            is_active=True,
        )
        serializer.save(created_by_member=member)


class DonorGroupMemberViewSet(viewsets.ModelViewSet):
    serializer_class = DonorGroupMemberSerializer
    permission_classes = [IsReadOnlyOrDonorGroupMemberManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = DonorGroupMember.objects.select_related(
            "donor_group",
            "donor_group__collection",
            "donor_group__collection__organization",
            "donor_group__collection__created_by_member",
            "donor_group__collection__created_by_member__user",
            "user",
        )
        donor_group_id = self.request.query_params.get("donor_group")
        if donor_group_id:
            queryset = queryset.filter(donor_group_id=donor_group_id)
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset


class DonorGroupItemViewSet(viewsets.ModelViewSet):
    serializer_class = DonorGroupItemSerializer
    permission_classes = [IsReadOnlyOrDonorGroupItemManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = DonorGroupItem.objects.select_related(
            "donor_group",
            "donor_group__collection",
            "donor_group__collection__organization",
            "donor_group__collection__created_by_member",
            "donor_group__collection__created_by_member__user",
            "user_item",
            "user_item__user",
            "user_item__category",
        )
        donor_group_id = self.request.query_params.get("donor_group")
        if donor_group_id:
            queryset = queryset.filter(donor_group_id=donor_group_id)
        user_item_id = self.request.query_params.get("user_item")
        if user_item_id:
            queryset = queryset.filter(user_item_id=user_item_id)
        return queryset


class CourierProfileViewSet(viewsets.ModelViewSet):
    serializer_class = CourierProfileSerializer
    permission_classes = [IsReadOnlyOrCourierProfileOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = CourierProfile.objects.select_related("user")
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

    def perform_create(self, serializer):
        if CourierProfile.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError(
                {"user": "Courier profile already exists for this user."}
            )
        serializer.save(user=self.request.user)


class MeetingPlaceProposalViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingPlaceProposalSerializer
    permission_classes = [IsReadOnlyOrMeetingPlaceProposalOwnerOrGroupManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = MeetingPlaceProposal.objects.select_related(
            "donor_group",
            "donor_group__collection",
            "donor_group__collection__organization",
            "donor_group__collection__created_by_member",
            "donor_group__collection__created_by_member__user",
            "proposed_by",
            "geodata",
            "geodata__city",
            "geodata__city__region",
        )
        donor_group_id = self.request.query_params.get("donor_group")
        if donor_group_id:
            queryset = queryset.filter(donor_group_id=donor_group_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(proposed_by=self.request.user)


class PollViewSet(viewsets.ModelViewSet):
    serializer_class = PollSerializer
    permission_classes = [IsReadOnlyOrPollManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = Poll.objects.select_related(
            "donor_group",
            "donor_group__collection",
            "donor_group__collection__organization",
            "donor_group__collection__created_by_member",
            "donor_group__collection__created_by_member__user",
            "news",
            "news__organization",
            "news__created_by_member",
            "news__created_by_member__user",
            "created_by_member",
            "created_by_member__user",
            "source_poll",
        ).prefetch_related(
            "options",
            "options__geodata",
            "options__source_place_proposal",
        )
        donor_group_id = self.request.query_params.get("donor_group")
        if donor_group_id:
            queryset = queryset.filter(donor_group_id=donor_group_id)
        news_id = self.request.query_params.get("news")
        if news_id:
            queryset = queryset.filter(news_id=news_id)
        kind = self.request.query_params.get("kind")
        if kind:
            queryset = queryset.filter(kind=kind)
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset

    def perform_create(self, serializer):
        created_by_member = self._get_created_by_member(serializer.validated_data)
        poll = serializer.save(created_by_member=created_by_member)
        self._notify_donor_group_members(poll)

    @action(detail=True, methods=["post"])
    def repost(self, request, pk=None):
        source_poll = self.get_object()
        serializer = PollRepostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        voted_options = source_poll.options.annotate(
            votes_count=Count("votes"),
        ).filter(votes_count__gt=0)
        if not voted_options.exists():
            return Response(
                {"detail": "Cannot repost a poll without voted options."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            new_poll = Poll.objects.create(
                donor_group=source_poll.donor_group,
                news=source_poll.news,
                created_by_member=self._get_created_by_member(
                    {
                        "donor_group": source_poll.donor_group,
                        "news": source_poll.news,
                    }
                ),
                source_poll=source_poll,
                title=serializer.validated_data.get("title") or source_poll.title,
                description=serializer.validated_data.get(
                    "description",
                    source_poll.description,
                ),
                kind=source_poll.kind,
                status=serializer.validated_data["status"],
                closes_at=serializer.validated_data.get("closes_at"),
            )
            for index, option in enumerate(voted_options.order_by("sort_order", "id")):
                PollOption.objects.create(
                    poll=new_poll,
                    text=option.text,
                    starts_at=option.starts_at,
                    ends_at=option.ends_at,
                    geodata=option.geodata,
                    place_street=option.place_street,
                    place_description=option.place_description,
                    source_place_proposal=option.source_place_proposal,
                    sort_order=index,
                )
        self._notify_donor_group_members(new_poll)
        response_serializer = self.get_serializer(new_poll)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="from-place-proposals")
    def from_place_proposals(self, request):
        serializer = PlaceProposalPollCreateSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        donor_group = serializer.validated_data["donor_group"]
        proposals = MeetingPlaceProposal.objects.filter(donor_group=donor_group)
        proposal_ids = serializer.validated_data.get("proposal_ids")
        if proposal_ids:
            proposals = proposals.filter(id__in=proposal_ids)
            if proposals.count() != len(set(proposal_ids)):
                return Response(
                    {"proposal_ids": "All proposals must belong to the donor group."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        proposals = list(proposals.order_by("created_at", "id"))
        if not proposals:
            return Response(
                {"detail": "No meeting place proposals found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            poll = Poll.objects.create(
                donor_group=donor_group,
                created_by_member=self._get_created_by_member({"donor_group": donor_group}),
                title=serializer.validated_data["title"],
                description=serializer.validated_data.get("description", ""),
                kind=Poll.Kind.PLACE,
                status=serializer.validated_data["status"],
                closes_at=serializer.validated_data.get("closes_at"),
            )
            for index, proposal in enumerate(proposals):
                PollOption.objects.create(
                    poll=poll,
                    geodata=proposal.geodata,
                    place_street=proposal.street,
                    place_description=proposal.description,
                    source_place_proposal=proposal,
                    sort_order=index,
                )
        self._notify_donor_group_members(poll)
        response_serializer = self.get_serializer(poll)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def _get_created_by_member(self, validated_data):
        donor_group = validated_data.get("donor_group")
        news = validated_data.get("news")
        organization = (
            donor_group.collection.organization
            if donor_group
            else news.organization
        )
        return OrganizationMember.objects.get(
            organization=organization,
            user=self.request.user,
            is_active=True,
        )

    def _notify_donor_group_members(self, poll):
        if not poll.donor_group_id or poll.status != Poll.Status.OPEN:
            return
        for member in poll.donor_group.members.select_related("user"):
            if member.user_id == poll.created_by_member.user_id:
                continue
            create_notification(
                recipient=member.user,
                actor=self.request.user,
                type="system",
                title="New donor group poll",
                body=poll.title,
                payload={
                    "target_type": "poll",
                    "target_id": poll.pk,
                    "donor_group_id": poll.donor_group_id,
                },
                send_push=True,
            )


class PollOptionViewSet(viewsets.ModelViewSet):
    serializer_class = PollOptionSerializer
    permission_classes = [IsReadOnlyOrPollOptionManager]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = PollOption.objects.select_related(
            "poll",
            "poll__donor_group",
            "poll__donor_group__collection",
            "poll__donor_group__collection__organization",
            "poll__donor_group__collection__created_by_member",
            "poll__donor_group__collection__created_by_member__user",
            "poll__news",
            "poll__news__organization",
            "poll__news__created_by_member",
            "poll__news__created_by_member__user",
            "geodata",
            "source_place_proposal",
        ).annotate(votes_count=Count("votes"))
        poll_id = self.request.query_params.get("poll")
        if poll_id:
            queryset = queryset.filter(poll_id=poll_id)
        return queryset


class PollVoteViewSet(viewsets.ModelViewSet):
    serializer_class = PollVoteSerializer
    permission_classes = [IsPollVoteOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = PollVote.objects.select_related(
            "poll",
            "poll__donor_group",
            "poll__donor_group__collection",
            "option",
            "user",
        ).filter(user=self.request.user)
        poll_id = self.request.query_params.get("poll")
        if poll_id:
            queryset = queryset.filter(poll_id=poll_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
