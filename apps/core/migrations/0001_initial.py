from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
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
                (
                    "name",
                    models.CharField(
                        max_length=100,
                        unique=True,
                        verbose_name="Название",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        allow_unicode=True,
                        blank=True,
                        max_length=100,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Описание"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Создано",
                    ),
                ),
            ],
            options={
                "verbose_name": "Категория",
                "verbose_name_plural": "Категории",
                "db_table": "categories",
                "ordering": ("name",),
            },
        ),
    ]
