from rest_framework.routers import DefaultRouter

from .views import InvitationViewSet, NotificationViewSet


router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("invitations", InvitationViewSet, basename="invitation")

urlpatterns = router.urls
