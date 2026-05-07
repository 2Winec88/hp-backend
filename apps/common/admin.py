from django.contrib import admin

from .models import City, GeoData, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "country_code", "geoname_id", "latitude", "longitude")
    list_filter = ("country_code",)
    search_fields = ("name", "country_code", "geoname_id")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "country_code", "geoname_id", "latitude", "longitude")
    list_filter = ("country_code", "region")
    search_fields = ("name", "region__name", "country_code", "geoname_id")
    autocomplete_fields = ("region",)


@admin.register(GeoData)
class GeoDataAdmin(admin.ModelAdmin):
    list_display = ("city", "street", "latitude", "longitude", "created_at")
    search_fields = ("city__name", "street")
    autocomplete_fields = ("city",)
