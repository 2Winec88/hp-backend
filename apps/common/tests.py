from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model

from .models import City, GeoData, Region


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
            geoname_id=1486209,
            defaults={
                "name": "Yekaterinburg",
                "latitude": "56.857500",
                "longitude": "60.612500",
                "country_code": "RU",
                "region": region,
            },
        )

        city_response = self.client.post(
            self.cities_url,
            data={
                "name": "Yekaterinburg",
                "geoname_id": 1486209,
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
