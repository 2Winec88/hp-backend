from rest_framework.routers import DefaultRouter

from .views import OrganizationRegistrationRequestViewSet


router = DefaultRouter()
router.register(
    "organization-registration-requests",
    OrganizationRegistrationRequestViewSet,
    basename="organization-registration-request",
)

urlpatterns = router.urls
