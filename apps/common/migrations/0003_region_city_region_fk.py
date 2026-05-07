import django.db.models.deletion
from django.db import migrations, models


def migrate_city_region_strings(apps, schema_editor):
    City = apps.get_model("common", "City")
    Region = apps.get_model("common", "Region")

    for city in City.objects.exclude(region="").iterator():
        region, _ = Region.objects.get_or_create(
            name=city.region,
            country_code=city.country_code,
        )
        city.region_ref_id = region.pk
        city.save(update_fields=("region_ref",))


def restore_city_region_strings(apps, schema_editor):
    City = apps.get_model("common", "City")

    for city in City.objects.select_related("region").iterator():
        if city.region_id:
            city.region_text = city.region.name
            city.save(update_fields=("region_text",))


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0002_seed_test_russian_cities"),
    ]

    operations = [
        migrations.CreateModel(
            name="Region",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=150)),
                (
                    "geoname_id",
                    models.PositiveIntegerField(blank=True, null=True, unique=True),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=6,
                        max_digits=9,
                        null=True,
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=6,
                        max_digits=9,
                        null=True,
                    ),
                ),
                ("country_code", models.CharField(blank=True, max_length=2)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "regions",
                "verbose_name": "Region",
                "verbose_name_plural": "Regions",
                "ordering": ("name", "country_code"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("name", "country_code"),
                        name="unique_region_name_country",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="city",
            name="region_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cities",
                to="common.region",
            ),
        ),
        migrations.RunPython(migrate_city_region_strings, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="city",
            name="unique_city_name_region_country",
        ),
        migrations.RenameField(
            model_name="city",
            old_name="region",
            new_name="region_text",
        ),
        migrations.RenameField(
            model_name="city",
            old_name="region_ref",
            new_name="region",
        ),
        migrations.RemoveField(
            model_name="city",
            name="region_text",
        ),
        migrations.AlterModelOptions(
            name="city",
            options={
                "ordering": ("name", "region__name", "country_code"),
                "verbose_name": "City",
                "verbose_name_plural": "Cities",
            },
        ),
        migrations.AddConstraint(
            model_name="city",
            constraint=models.UniqueConstraint(
                fields=("name", "region", "country_code"),
                name="unique_city_name_region_country",
            ),
        ),
    ]
