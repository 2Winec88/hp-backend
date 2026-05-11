from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BranchItemViewSet,
    CollectionItemViewSet,
    CollectionViewSet,
    CourierProfileViewSet,
    DonorGroupItemViewSet,
    DonorGroupMemberViewSet,
    DonorGroupVideoReportViewSet,
    DonorGroupViewSet,
    DeliveredItemViewSet,
    ItemCategoryViewSet,
    MeetingPlaceProposalViewSet,
    PollOptionViewSet,
    PollViewSet,
    PollVoteViewSet,
    UserItemViewSet,
    UserItemImageViewSet,
)

router = DefaultRouter()
router.register("item-categories", ItemCategoryViewSet, basename="item-category")
router.register("user-items", UserItemViewSet, basename="user-item")
router.register("user-item-images", UserItemImageViewSet, basename="user-item-image")
router.register("collections", CollectionViewSet, basename="collection")
router.register("collection-items", CollectionItemViewSet, basename="collection-item")
router.register("branch-items", BranchItemViewSet, basename="branch-item")
router.register("donor-groups", DonorGroupViewSet, basename="donor-group")
router.register("donor-group-members", DonorGroupMemberViewSet, basename="donor-group-member")
router.register("donor-group-items", DonorGroupItemViewSet, basename="donor-group-item")
router.register("delivered-items", DeliveredItemViewSet, basename="delivered-item")
router.register("donor-group-video-reports", DonorGroupVideoReportViewSet, basename="donor-group-video-report")
router.register("courier-profiles", CourierProfileViewSet, basename="courier-profile")
router.register("meeting-place-proposals", MeetingPlaceProposalViewSet, basename="meeting-place-proposal")
router.register("polls", PollViewSet, basename="poll")
router.register("poll-options", PollOptionViewSet, basename="poll-option")
router.register("poll-votes", PollVoteViewSet, basename="poll-vote")

urlpatterns = [
    path("", include(router.urls)),
]
