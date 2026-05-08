import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.common.models import City, Region


class Command(BaseCommand):
    help = "Import Russian regions and cities from JSON datasets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--regions",
            default=str(Path(settings.BASE_DIR) / "docs" / "russia-regions.json"),
            help="Path to russia-regions.json.",
        )
        parser.add_argument(
            "--cities",
            default=str(Path(settings.BASE_DIR) / "docs" / "russia-cities.json"),
            help="Path to russia-cities.json.",
        )
        parser.add_argument(
            "--country-code",
            default="RU",
            help="Country code to write into Region and City rows.",
        )

    def handle(self, *args, **options):
        regions_path = Path(options["regions"])
        cities_path = Path(options["cities"])
        country_code = options["country_code"].strip().upper()

        self._validate_file(regions_path)
        self._validate_file(cities_path)

        regions_data = self._load_json(regions_path)
        cities_data = self._load_json(cities_path)

        with transaction.atomic():
            region_stats, regions_by_key = self._import_regions(
                regions_data,
                country_code,
            )
            city_stats = self._import_cities(
                cities_data,
                regions_by_key,
                country_code,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Russia locations import completed: "
                f"regions created={region_stats['created']}, "
                f"regions updated={region_stats['updated']}, "
                f"cities created={city_stats['created']}, "
                f"cities updated={city_stats['updated']}, "
                f"cities skipped_without_region={city_stats['skipped_without_region']}."
            )
        )

    def _validate_file(self, path):
        if not path.exists():
            raise CommandError(f"Dataset file does not exist: {path}")
        if not path.is_file():
            raise CommandError(f"Dataset path is not a file: {path}")

    def _load_json(self, path):
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {path}: {exc}") from exc

        if not isinstance(data, list):
            raise CommandError(f"Expected a JSON array in {path}.")
        return data

    def _import_regions(self, regions_data, country_code):
        stats = {"created": 0, "updated": 0}
        regions_by_key = {}

        for item in regions_data:
            name = self._normalize_name(item.get("name"))
            if not name:
                continue

            region, created = Region.objects.update_or_create(
                name=name,
                country_code=country_code,
                defaults={
                    "geoname_id": None,
                    "latitude": None,
                    "longitude": None,
                },
            )
            stats["created" if created else "updated"] += 1
            self._index_region(regions_by_key, region, item)

        return stats, regions_by_key

    def _import_cities(self, cities_data, regions_by_key, country_code):
        stats = {"created": 0, "updated": 0, "skipped_without_region": 0}

        for item in cities_data:
            name = self._normalize_name(item.get("name"))
            if not name:
                continue

            region = self._resolve_region(item.get("region") or {}, regions_by_key)
            if region is None:
                stats["skipped_without_region"] += 1
                continue

            coords = item.get("coords") or {}
            city, created = City.objects.update_or_create(
                name=name,
                region=region,
                country_code=country_code,
                defaults={
                    "geoname_id": None,
                    "latitude": self._coordinate(coords.get("lat")),
                    "longitude": self._coordinate(coords.get("lon")),
                },
            )
            stats["created" if created else "updated"] += 1

        return stats

    def _index_region(self, regions_by_key, region, item):
        keys = [
            item.get("name"),
            item.get("fullname"),
            item.get("label"),
            item.get("id"),
            item.get("guid"),
            item.get("code"),
            item.get("iso_3166-2"),
        ]
        for key in keys:
            normalized_key = self._normalize_key(key)
            if normalized_key:
                regions_by_key[normalized_key] = region

    def _resolve_region(self, region_data, regions_by_key):
        keys = [
            region_data.get("name"),
            region_data.get("fullname"),
            region_data.get("label"),
            region_data.get("id"),
            region_data.get("guid"),
            region_data.get("code"),
            region_data.get("iso_3166-2"),
        ]
        for key in keys:
            region = regions_by_key.get(self._normalize_key(key))
            if region:
                return region
        return None

    def _normalize_name(self, value):
        if value is None:
            return ""
        return str(value).strip()[:150]

    def _normalize_key(self, value):
        if value is None:
            return ""
        return str(value).strip().casefold()

    def _coordinate(self, value):
        if value in (None, ""):
            return None
        return str(value)
