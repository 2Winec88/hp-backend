from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    class Scope(models.TextChoices):
        EVENT = "event", "Мероприятия"
        FUNDRAISING = "fundraising", "Сборы"

    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(
        max_length=100,
        blank=True,
        allow_unicode=True,
        verbose_name="Slug",
    )
    scope = models.CharField(
        max_length=20,
        choices=Scope.choices,
        verbose_name="Область",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        db_table = "categories"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("scope", "name"),
                name="unique_category_name_per_scope",
            ),
            models.UniqueConstraint(
                fields=("scope", "slug"),
                name="unique_category_slug_per_scope",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
