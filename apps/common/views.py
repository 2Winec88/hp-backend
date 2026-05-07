from rest_framework import filters, permissions, viewsets

from .models import City, GeoData, Region
from .serializers import CitySerializer, GeoDataSerializer, RegionSerializer


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "head", "options"]
    filter_backends = [filters.SearchFilter]
    search_fields = ("name", "country_code")


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.select_related("region")
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "head", "options"]
    filter_backends = [filters.SearchFilter]
    search_fields = ("name", "region__name", "country_code")


class GeoDataViewSet(viewsets.ModelViewSet):
    queryset = GeoData.objects.select_related("city", "city__region")
    serializer_class = GeoDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
