from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    EventImageViewSet,
    EventNewsViewSet,
    EventViewSet,
    OrganizationBranchImageViewSet,
    OrganizationBranchViewSet,
    OrganizationViewSet,
    OrganizationMemberViewSet,
    OrganizationNewsCommentViewSet,
    OrganizationNewsImageViewSet,
    OrganizationNewsViewSet,
    OrganizationReportDocumentViewSet,
    OrganizationRegistrationRequestViewSet,
)


router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("members", OrganizationMemberViewSet, basename="organization-member")
router.register("branches", OrganizationBranchViewSet, basename="organization-branch")
router.register("branch-images", OrganizationBranchImageViewSet, basename="organization-branch-image")
router.register("events", EventViewSet, basename="event")
router.register("event-images", EventImageViewSet, basename="event-image")
router.register("news", OrganizationNewsViewSet, basename="organization-news")
router.register("news-images", OrganizationNewsImageViewSet, basename="organization-news-image")
router.register("news-comments", OrganizationNewsCommentViewSet, basename="organization-news-comment")
router.register("report-documents", OrganizationReportDocumentViewSet, basename="organization-report-document")
router.register("event-news", EventNewsViewSet, basename="event-news")
router.register(
    "organization-registration-requests",
    OrganizationRegistrationRequestViewSet,
    basename="organization-registration-request",
)

urlpatterns = router.urls
