from rest_framework.routers import DefaultRouter

from .views import EventNewsViewSet, EventViewSet, OrganizationRegistrationRequestViewSet


router = DefaultRouter()
router.register("events", EventViewSet, basename="event")
router.register("event-news", EventNewsViewSet, basename="event-news")
router.register(
    "organization-registration-requests",
    OrganizationRegistrationRequestViewSet,
    basename="organization-registration-request",
)

urlpatterns = router.urls
