from rest_framework.routers import DefaultRouter

from .views import (
    InvitationViewSet,
    NotificationDeliveryViewSet,
    NotificationViewSet,
    UserDeviceViewSet,
)


router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("notification-deliveries", NotificationDeliveryViewSet, basename="notification-delivery")
router.register("devices", UserDeviceViewSet, basename="user-device")
router.register("invitations", InvitationViewSet, basename="invitation")

urlpatterns = router.urls
