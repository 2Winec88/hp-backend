from django.db import migrations


TEST_RUSSIAN_CITIES = [
    {
        "name": "Kaliningrad",
        "geoname_id": 554234,
        "latitude": "54.706490",
        "longitude": "20.510950",
        "country_code": "RU",
        "region": "Kaliningrad Oblast",
    },
    {
        "name": "Murmansk",
        "geoname_id": 524305,
        "latitude": "68.979170",
        "longitude": "33.092510",
        "country_code": "RU",
        "region": "Murmansk Oblast",
    },
    {
        "name": "Saint Petersburg",
        "geoname_id": 498817,
        "latitude": "59.938630",
        "longitude": "30.314130",
        "country_code": "RU",
        "region": "Saint Petersburg",
    },
    {
        "name": "Moscow",
        "geoname_id": 524901,
        "latitude": "55.752220",
        "longitude": "37.615560",
        "country_code": "RU",
        "region": "Moscow",
    },
    {
        "name": "Sochi",
        "geoname_id": 491422,
        "latitude": "43.599170",
        "longitude": "39.725690",
        "country_code": "RU",
        "region": "Krasnodar Krai",
    },
    {
        "name": "Yekaterinburg",
        "geoname_id": 1486209,
        "latitude": "56.857500",
        "longitude": "60.612500",
        "country_code": "RU",
        "region": "Sverdlovsk Oblast",
    },
    {
        "name": "Novosibirsk",
        "geoname_id": 1496747,
        "latitude": "55.041500",
        "longitude": "82.934600",
        "country_code": "RU",
        "region": "Novosibirsk Oblast",
    },
    {
        "name": "Yakutsk",
        "geoname_id": 2013159,
        "latitude": "62.033890",
        "longitude": "129.733060",
        "country_code": "RU",
        "region": "Sakha Republic",
    },
    {
        "name": "Vladivostok",
        "geoname_id": 2013348,
        "latitude": "43.105620",
        "longitude": "131.873530",
        "country_code": "RU",
        "region": "Primorsky Krai",
    },
    {
        "name": "Petropavlovsk-Kamchatsky",
        "geoname_id": 2122104,
        "latitude": "53.044440",
        "longitude": "158.650760",
        "country_code": "RU",
        "region": "Kamchatka Krai",
    },
]


def seed_test_russian_cities(apps, schema_editor):
    City = apps.get_model("common", "City")
    for city in TEST_RUSSIAN_CITIES:
        City.objects.update_or_create(
            geoname_id=city["geoname_id"],
            defaults={
                "name": city["name"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "country_code": city["country_code"],
                "region": city["region"],
            },
        )


def unseed_test_russian_cities(apps, schema_editor):
    City = apps.get_model("common", "City")
    City.objects.filter(
        geoname_id__in=[city["geoname_id"] for city in TEST_RUSSIAN_CITIES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_test_russian_cities, unseed_test_russian_cities),
    ]
