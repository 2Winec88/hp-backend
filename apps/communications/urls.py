from rest_framework.routers import DefaultRouter

from .views import (
    DonorGroupMessageViewSet,
    InvitationViewSet,
    NotificationDeliveryViewSet,
    NotificationViewSet,
    OrganizationMessageViewSet,
    UserDeviceViewSet,
)


router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("notification-deliveries", NotificationDeliveryViewSet, basename="notification-delivery")
router.register("devices", UserDeviceViewSet, basename="user-device")
router.register("invitations", InvitationViewSet, basename="invitation")
router.register("organization-messages", OrganizationMessageViewSet, basename="organization-message")
router.register("donor-group-messages", DonorGroupMessageViewSet, basename="donor-group-message")

urlpatterns = router.urls
