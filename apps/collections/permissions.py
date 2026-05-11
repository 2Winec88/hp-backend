from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.permissions import is_active_organization_manager


def is_collection_author_or_manager(*, collection, user):
    if not user or not user.is_authenticated:
        return False
    if (
        collection.created_by_member.user_id == user.id
        and collection.created_by_member.is_active
    ):
        return True
    return is_active_organization_manager(
        organization=collection.organization,
        user=user,
    )


def is_donor_group_collection_author_or_manager(*, donor_group, user):
    return is_collection_author_or_manager(
        collection=donor_group.collection,
        user=user,
    )


def is_donor_group_member(*, donor_group, user):
    if not user or not user.is_authenticated:
        return False
    return donor_group.members.filter(user=user).exists()


def is_donor_group_item_owner(*, donor_group_item, user):
    if not user or not user.is_authenticated:
        return False
    return donor_group_item.user_item.user_id == user.id


def is_poll_manager(*, poll, user):
    if poll.donor_group_id:
        return is_donor_group_collection_author_or_manager(
            donor_group=poll.donor_group,
            user=user,
        )
    if poll.news_id:
        if not user or not user.is_authenticated:
            return False
        return is_active_organization_manager(
            organization=poll.news.organization,
            user=user,
        ) or (
            poll.news.created_by_member.user_id == user.id
            and poll.news.created_by_member.is_active
        )
    return False


class IsReadOnlyOrUserItemOwner(BasePermission):
    message = "Only the item owner can edit this user item."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and obj.user_id == user.id)


class IsReadOnlyOrUserItemImageOwner(BasePermission):
    message = "Only the item owner can edit this user item image."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and obj.user_item.user_id == user.id
        )


class IsReadOnlyOrCollectionAuthorOrOrganizationManager(BasePermission):
    message = "Only the collection author or an organization manager can edit this collection."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return is_collection_author_or_manager(collection=obj, user=request.user)


class IsReadOnlyOrCollectionItemAuthorOrOrganizationManager(BasePermission):
    message = "Only the collection author or an organization manager can edit this collection item."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return is_collection_author_or_manager(
            collection=obj.collection,
            user=request.user,
        )


class IsReadOnlyOrBranchItemOrganizationManager(BasePermission):
    message = "Only an active organization manager can edit this branch item."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return is_active_organization_manager(
            organization=obj.branch.organization,
            user=user,
        )


class IsReadOnlyOrDonorGroupCollectionAuthorOrOrganizationManager(BasePermission):
    message = "Only the collection author or an organization manager can edit this donor group."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return is_donor_group_collection_author_or_manager(
            donor_group=obj,
            user=request.user,
        )


class IsReadOnlyOrDonorGroupMemberManager(BasePermission):
    message = "Only the collection author or an organization manager can manage donor group members."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return is_donor_group_collection_author_or_manager(
            donor_group=obj.donor_group,
            user=request.user,
        )


class IsReadOnlyOrDonorGroupItemManager(BasePermission):
    message = "Only the item owner, collection author, or organization manager can manage active donor group items."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if obj.donor_group.is_delivery_completed:
            return False
        if is_donor_group_item_owner(donor_group_item=obj, user=request.user):
            return True
        return is_donor_group_collection_author_or_manager(
            donor_group=obj.donor_group,
            user=request.user,
        )


class IsReadOnlyOrCourierProfileOwner(BasePermission):
    message = "Only the courier profile owner can edit this profile."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and obj.user_id == user.id)


class IsReadOnlyOrPollManager(BasePermission):
    message = "Only the poll organizer or an organization manager can edit this poll."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return is_poll_manager(poll=obj, user=request.user)


class IsReadOnlyOrPollOptionManager(BasePermission):
    message = "Only the poll organizer or an organization manager can edit poll options."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return is_poll_manager(poll=obj.poll, user=request.user)


class IsReadOnlyOrMeetingPlaceProposalOwnerOrGroupManager(BasePermission):
    message = "Only the proposal author or group manager can edit this proposal."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if obj.proposed_by_id == getattr(user, "id", None):
            return True
        return is_donor_group_collection_author_or_manager(
            donor_group=obj.donor_group,
            user=user,
        )


class IsPollVoteOwner(BasePermission):
    message = "Only the voter can edit this vote."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and obj.user_id == user.id)
