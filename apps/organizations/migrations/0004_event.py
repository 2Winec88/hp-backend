import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_category_scope"),
        ("organizations", "0003_update_common_document_upload_to"),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
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
                ("title", models.CharField(max_length=200, verbose_name="Название")),
                (
                    "slug",
                    models.SlugField(
                        allow_unicode=True,
                        blank=True,
                        max_length=200,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                ("content", models.TextField(verbose_name="Описание")),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="events/",
                        verbose_name="Изображение",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Черновик"),
                            ("published", "Опубликовано"),
                        ],
                        default="draft",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                ("starts_at", models.DateTimeField(verbose_name="Дата начала")),
                (
                    "ends_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Дата окончания",
                    ),
                ),
                ("city", models.CharField(blank=True, max_length=100, verbose_name="Город")),
                ("is_online", models.BooleanField(default=False, verbose_name="Онлайн")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создано"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Обновлено"),
                ),
                (
                    "published_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Опубликовано",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        limit_choices_to={"scope": "event"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="events",
                        to="core.category",
                        verbose_name="Категория",
                    ),
                ),
                (
                    "created_by_member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_events",
                        to="organizations.organizationmember",
                        verbose_name="Создатель",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="organizations.organization",
                        verbose_name="Организация",
                    ),
                ),
            ],
            options={
                "verbose_name": "Мероприятие",
                "verbose_name_plural": "Мероприятия",
                "db_table": "events",
                "ordering": ("-starts_at", "-created_at"),
            },
        ),
    ]
