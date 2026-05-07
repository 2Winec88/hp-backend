from rest_framework import serializers

from .models import City, GeoData, Region, validate_coordinates


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = (
            "id",
            "name",
            "geoname_id",
            "latitude",
            "longitude",
            "country_code",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CitySerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source="region.name", read_only=True)

    class Meta:
        model = City
        fields = (
            "id",
            "name",
            "geoname_id",
            "latitude",
            "longitude",
            "country_code",
            "region",
            "region_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "region_name", "created_at", "updated_at")

    def validate(self, attrs):
        validate_coordinates(attrs.get("latitude"), attrs.get("longitude"))
        return attrs


class GeoDataSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    region_name = serializers.CharField(source="city.region.name", read_only=True)

    class Meta:
        model = GeoData
        fields = (
            "id",
            "city",
            "city_name",
            "region_name",
            "street",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "city_name", "region_name", "created_at", "updated_at")

    def validate(self, attrs):
        validate_coordinates(attrs.get("latitude"), attrs.get("longitude"))
        return attrs
