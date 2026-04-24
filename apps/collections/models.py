from django.db import models


class ItemCategory(models.Model):
    class Unit(models.TextChoices):
        PIECE = "piece", "Штуки"
        PACK = "pack", "Упаковки"
        BOX = "box", "Коробки"
        KG = "kg", "Килограммы"
        LITER = "liter", "Литры"

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
        default=Unit.PIECE,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item category"
        verbose_name_plural = "Item categories"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Item(models.Model):
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("category", "name"),
                name="unique_item_name_per_category",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"
