from django.db import migrations


ITEM_CATEGORIES = [
    ("Зубная гигиена", "зубная паста, зубные щётки"),
    ("Мыло и базовая гигиена", "мыло, шампунь, влажные салфетки"),
    ("Питьевая вода", "бутылки воды, канистры, вода 5 л"),
    ("Крупы и макароны", "рис, гречка, макароны"),
    ("Мясные консервы", "тушёнка, паштеты, рыбные консервы"),
    ("Постельное бельё", "простыни, наволочки, пододеяльники"),
    ("Батарейки и аккумуляторы", "AA, AAA, аккумуляторные элементы"),
    ("Одеяла и пледы", "одеяла, флисовые пледы"),
    ("Зарядные устройства", "зарядки для телефонов, кабели, автомобильные зарядки"),
    ("Футболки и кофты", "футболки, толстовки, свитеры"),
    ("Фонарики", "ручные фонари, налобные фонари"),
    ("Брюки", "спортивные штаны, брюки, джинсы"),
    ("Спальные мешки", "летние и утеплённые спальники"),
    ("Обувь", "ботинки, сапоги, кроссовки"),
    ("Куртки", "демисезонные и зимние куртки"),
    ("Электрообогреватели", "масляные, конвекторные обогреватели"),
    ("Генераторы", "бензиновые генераторы"),
]


def seed_item_categories(apps, schema_editor):
    item_category_model = apps.get_model("collections", "ItemCategory")
    for name, description in ITEM_CATEGORIES:
        item_category_model.objects.update_or_create(
            name=name,
            defaults={
                "description": description,
                "unit": "piece",
                "is_active": True,
            },
        )


def unseed_item_categories(apps, schema_editor):
    item_category_model = apps.get_model("collections", "ItemCategory")
    item_category_model.objects.filter(
        name__in=[name for name, _description in ITEM_CATEGORIES],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("collections", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_item_categories, unseed_item_categories),
    ]
