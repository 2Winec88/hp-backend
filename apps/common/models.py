from django.core.exceptions import ValidationError
from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=150)
    geoname_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    country_code = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "regions"
        verbose_name = "Region"
        verbose_name_plural = "Regions"
        ordering = ("name", "country_code")
        constraints = [
            models.UniqueConstraint(
                fields=("name", "country_code"),
                name="unique_region_name_country",
            )
        ]

    def __str__(self):
        if self.country_code:
            return f"{self.name} ({self.country_code})"
        return self.name

    def clean(self):
        super().clean()
        validate_coordinates(self.latitude, self.longitude)


class City(models.Model):
    name = models.CharField(max_length=150)
    geoname_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    country_code = models.CharField(max_length=2, blank=True)
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cities",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cities"
        verbose_name = "City"
        verbose_name_plural = "Cities"
        ordering = ("name", "region__name", "country_code")
        constraints = [
            models.UniqueConstraint(
                fields=("name", "region", "country_code"),
                name="unique_city_name_region_country",
            )
        ]

    def __str__(self):
        region_name = self.region.name if self.region_id else ""
        location_parts = [part for part in (region_name, self.country_code) if part]
        if location_parts:
            return f"{self.name} ({', '.join(location_parts)})"
        return self.name

    def clean(self):
        super().clean()
        validate_coordinates(self.latitude, self.longitude)


class GeoData(models.Model):
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="geo_data",
    )
    street = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "geo_data"
        verbose_name = "Geo data"
        verbose_name_plural = "Geo data"
        ordering = ("city__name", "street", "id")

    def __str__(self):
        parts = []
        if self.city_id:
            parts.append(self.city.name)
        if self.street:
            parts.append(self.street)
        if not parts and self.latitude is not None and self.longitude is not None:
            parts.append(f"{self.latitude}, {self.longitude}")
        return ", ".join(parts) or f"GeoData #{self.pk}"

    def clean(self):
        super().clean()
        validate_coordinates(self.latitude, self.longitude)


def validate_coordinates(latitude, longitude):
    if latitude is not None and not (-90 <= latitude <= 90):
        raise ValidationError({"latitude": "Latitude must be between -90 and 90."})
    if longitude is not None and not (-180 <= longitude <= 180):
        raise ValidationError({"longitude": "Longitude must be between -180 and 180."})
