from django.test import TestCase

from .models import Category


class CoreCategoryTests(TestCase):
    def test_category_generates_slug_from_name(self):
        category = Category.objects.create(
            name="Помощь детям",
            scope=Category.Scope.EVENT,
        )

        self.assertEqual(category.slug, "помощь-детям")

    def test_category_preserves_explicit_slug(self):
        category = Category.objects.create(
            name="Помощь детям",
            slug="children-help",
            scope=Category.Scope.EVENT,
        )

        self.assertEqual(category.slug, "children-help")

    def test_category_orders_by_name(self):
        Category.objects.create(name="Спорт", scope=Category.Scope.EVENT)
        Category.objects.create(name="Дети", scope=Category.Scope.EVENT)

        self.assertEqual(
            list(Category.objects.values_list("name", flat=True)),
            ["Дети", "Спорт"],
        )

    def test_category_can_reuse_name_and_slug_in_different_scopes(self):
        event_category = Category.objects.create(
            name="Спорт",
            scope=Category.Scope.EVENT,
        )
        fundraising_category = Category.objects.create(
            name="Спорт",
            scope=Category.Scope.FUNDRAISING,
        )

        self.assertEqual(event_category.slug, fundraising_category.slug)
        self.assertEqual(
            list(Category.objects.filter(scope=Category.Scope.EVENT)),
            [event_category],
        )
        self.assertEqual(
            list(Category.objects.filter(scope=Category.Scope.FUNDRAISING)),
            [fundraising_category],
        )
