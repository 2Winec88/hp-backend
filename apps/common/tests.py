import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import Workbook
from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from .models import City, GeoData, Region


class ImportRussiaLocationsCommandTests(TestCase):
    def test_imports_regions_and_cities_from_json_datasets(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            regions_path = temp_path / "regions.json"
            cities_path = temp_path / "cities.json"
            regions_path.write_text(
                json.dumps(
                    [
                        {
                            "name": "Тестовая область",
                            "label": "test_region",
                            "id": "9900000000000",
                            "guid": "region-guid",
                            "code": "99",
                            "iso_3166-2": "RU-TEST",
                            "fullname": "Тестовая область",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            cities_path.write_text(
                json.dumps(
                    [
                        {
                            "name": "Тестоград",
                            "coords": {"lat": 56.123456, "lon": 60.654321},
                            "region": {
                                "name": "Тестовая область",
                                "label": "test_region",
                                "id": "9900000000000",
                                "guid": "region-guid",
                                "code": "99",
                                "iso_3166-2": "RU-TEST",
                            },
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            call_command(
                "import_russia_locations",
                regions=str(regions_path),
                cities=str(cities_path),
            )

        region = Region.objects.get(name="Тестовая область", country_code="RU")
        city = City.objects.get(name="Тестоград", region=region, country_code="RU")
        self.assertEqual(str(city.latitude), "56.123456")
        self.assertEqual(str(city.longitude), "60.654321")

    def test_import_updates_existing_rows_without_duplicates(self):
        region = Region.objects.create(name="Тестовая область", country_code="RU")
        City.objects.create(
            name="Тестоград",
            region=region,
            country_code="RU",
            latitude="55.000000",
            longitude="61.000000",
        )

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            regions_path = temp_path / "regions.json"
            cities_path = temp_path / "cities.json"
            regions_path.write_text(
                json.dumps([{"name": "Тестовая область", "label": "test_region"}], ensure_ascii=False),
                encoding="utf-8",
            )
            cities_path.write_text(
                json.dumps(
                    [
                        {
                            "name": "Тестоград",
                            "coords": {"lat": 56.111111, "lon": 60.222222},
                            "region": {"label": "test_region"},
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            call_command(
                "import_russia_locations",
                regions=str(regions_path),
                cities=str(cities_path),
            )

        self.assertEqual(
            Region.objects.filter(name="Тестовая область", country_code="RU").count(),
            1,
        )
        self.assertEqual(
            City.objects.filter(name="Тестоград", region=region, country_code="RU").count(),
            1,
        )
        city = City.objects.get(name="Тестоград")
        self.assertEqual(str(city.latitude), "56.111111")
        self.assertEqual(str(city.longitude), "60.222222")


class ImportAllsettlementsLocationsCommandTests(TestCase):
    headers = (
        "object_level",
        "object_name",
        "region",
        "settlement",
        "latitude_dadata",
        "longitude_dadata",
    )

    def test_imports_settlements_without_creating_duplicates(self):
        Region.objects.create(name="Республика Тест", country_code="RU")

        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir) / "allsettlements.xlsx"
            self._write_dataset(
                dataset_path,
                [
                    (
                        "Регион",
                        "Республика Тест",
                        "Республика Тест",
                        "",
                        "",
                        "",
                    ),
                    (
                        "Населенный пункт",
                        "поселок Новый",
                        "Республика Тест",
                        "поселок Новый",
                        "56.1234564",
                        "60.6543214",
                    ),
                    (
                        "Населенный пункт",
                        "поселок Новый",
                        "Республика Тест",
                        "поселок Новый",
                        "57.000000",
                        "61.000000",
                    ),
                ],
            )

            call_command("import_allsettlements_locations", file=str(dataset_path))
            call_command("import_allsettlements_locations", file=str(dataset_path))

        city = City.objects.get(name="поселок Новый")
        self.assertEqual(
            City.objects.filter(
                name="поселок Новый",
                region=city.region,
                country_code="RU",
            ).count(),
            1,
        )
        self.assertEqual(str(city.latitude), "56.123456")
        self.assertEqual(str(city.longitude), "60.654321")

    def test_updates_existing_city_and_supports_dry_run(self):
        region = Region.objects.create(name="Республика Тест", country_code="RU")
        City.objects.create(
            name="село Старое",
            region=region,
            country_code="RU",
            latitude="55.000000",
            longitude="59.000000",
        )

        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir) / "allsettlements.xlsx"
            self._write_dataset(
                dataset_path,
                [
                    (
                        "Населенный пункт",
                        "село Старое",
                        "Республика Тест",
                        "село Старое",
                        "56.111111",
                        "60.222222",
                    ),
                    (
                        "Населенный пункт",
                        "деревня Без региона",
                        "Неизвестная область",
                        "деревня Без региона",
                        "57.000000",
                        "61.000000",
                    ),
                ],
            )

            output = StringIO()
            call_command(
                "import_allsettlements_locations",
                file=str(dataset_path),
                dry_run=True,
                stdout=output,
            )
            city = City.objects.get(name="село Старое")
            self.assertEqual(str(city.latitude), "55.000000")

            call_command("import_allsettlements_locations", file=str(dataset_path))

        city = City.objects.get(name="село Старое")
        self.assertEqual(
            City.objects.filter(
                name="село Старое",
                region=region,
                country_code="RU",
            ).count(),
            1,
        )
        self.assertEqual(str(city.latitude), "56.111111")
        self.assertEqual(str(city.longitude), "60.222222")
        self.assertIn("skipped_without_region=1", output.getvalue())

    def _write_dataset(self, path, rows):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "data"
        worksheet.append(self.headers)
        for row in rows:
            worksheet.append(row)
        workbook.save(path)


class CommonGeoDataApiTests(APITestCase):
    cities_url = "/api/v1/common/cities/"
    geodata_url = "/api/v1/common/geodata/"

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="geo-user",
            email="geo-user@example.com",
            password="StrongPassword123!",
        )

    def test_city_api_is_read_only_and_geodata_can_reference_existing_city(self):
        self.client.force_authenticate(self.user)
        region, _ = Region.objects.get_or_create(
            name="Sverdlovsk Oblast",
            country_code="RU",
        )
        city, _ = City.objects.get_or_create(
            name="Yekaterinburg",
            region=region,
            country_code="RU",
            defaults={
                "latitude": "56.857500",
                "longitude": "60.612500",
            },
        )

        city_response = self.client.post(
            self.cities_url,
            data={
                "name": "Yekaterinburg",
                "latitude": "56.857500",
                "longitude": "60.612500",
                "country_code": "RU",
                "region": "Sverdlovsk Oblast",
            },
            format="json",
        )
        self.assertEqual(city_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        geodata_response = self.client.post(
            self.geodata_url,
            data={
                "city": city.pk,
                "street": "Lenina, 1",
                "latitude": "56.838011",
                "longitude": "60.597465",
            },
            format="json",
        )

        self.assertEqual(geodata_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(geodata_response.data["city_name"], "Yekaterinburg")
        self.assertEqual(geodata_response.data["region_name"], "Sverdlovsk Oblast")
        self.assertTrue(GeoData.objects.filter(street="Lenina, 1").exists())

    def test_city_api_supports_search_for_preloaded_cities(self):
        response = self.client.get(self.cities_url, data={"search": "vlad"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Vladivostok")
        self.assertEqual(response.data[0]["region_name"], "Primorsky Krai")

    def test_city_api_search_supports_city_region_and_limit_for_address_selection(self):
        first_region = Region.objects.create(name="Тестовая область", country_code="RU")
        second_region = Region.objects.create(name="Другой край", country_code="RU")
        City.objects.create(
            name="Тестоград",
            country_code="RU",
            region=first_region,
            latitude="56.000000",
            longitude="60.000000",
        )
        City.objects.create(
            name="Новый город",
            country_code="RU",
            region=first_region,
            latitude="57.000000",
            longitude="61.000000",
        )
        City.objects.create(
            name="Дальнегорск",
            country_code="RU",
            region=second_region,
            latitude="58.000000",
            longitude="62.000000",
        )

        city_response = self.client.get(self.cities_url, data={"search": "тесто"})
        region_response = self.client.get(
            self.cities_url,
            data={"search": "область", "limit": 1},
        )

        self.assertEqual(city_response.status_code, status.HTTP_200_OK)
        self.assertEqual(city_response.data[0]["name"], "Тестоград")
        self.assertEqual(city_response.data[0]["region_name"], "Тестовая область")
        self.assertEqual(region_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(region_response.data), 1)
        self.assertEqual(region_response.data[0]["region_name"], "Тестовая область")

    def test_region_api_is_read_only_and_supports_search(self):
        list_response = self.client.get("/api/v1/common/regions/", data={"search": "sver"})
        create_response = self.client.post(
            "/api/v1/common/regions/",
            data={"name": "Test Region", "country_code": "RU"},
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["name"], "Sverdlovsk Oblast")
        self.assertEqual(create_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_city_seed_contains_test_cities_across_russia(self):
        expected_names = {
            "Kaliningrad",
            "Murmansk",
            "Moscow",
            "Sochi",
            "Yekaterinburg",
            "Novosibirsk",
            "Yakutsk",
            "Vladivostok",
            "Petropavlovsk-Kamchatsky",
        }

        self.assertTrue(expected_names.issubset(set(City.objects.values_list("name", flat=True))))

    def test_geodata_rejects_coordinates_out_of_range(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.geodata_url,
            data={
                "latitude": "91.000000",
                "longitude": "60.000000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("latitude", response.data)
