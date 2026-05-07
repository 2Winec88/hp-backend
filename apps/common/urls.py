from rest_framework.routers import DefaultRouter

from .views import CityViewSet, GeoDataViewSet, RegionViewSet


router = DefaultRouter()
router.register("regions", RegionViewSet, basename="region")
router.register("cities", CityViewSet, basename="city")
router.register("geodata", GeoDataViewSet, basename="geodata")

urlpatterns = router.urls
