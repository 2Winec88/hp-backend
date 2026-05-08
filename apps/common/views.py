from django.db.models import Case, IntegerField, Q, Value, When
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

    def get_queryset(self):
        queryset = City.objects.select_related("region")
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(region__name__icontains=search)
                | Q(country_code__iexact=search)
            ).annotate(
                search_rank=Case(
                    When(name__istartswith=search, then=Value(0)),
                    When(name__icontains=search, then=Value(1)),
                    When(region__name__istartswith=search, then=Value(2)),
                    When(region__name__icontains=search, then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField(),
                )
            ).order_by("search_rank", "name", "region__name", "id")
        return queryset[: self._get_limit()]

    def _get_limit(self):
        raw_limit = self.request.query_params.get("limit", "20")
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return 20
        return min(max(limit, 1), 100)


class GeoDataViewSet(viewsets.ModelViewSet):
    queryset = GeoData.objects.select_related("city", "city__region")
    serializer_class = GeoDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
