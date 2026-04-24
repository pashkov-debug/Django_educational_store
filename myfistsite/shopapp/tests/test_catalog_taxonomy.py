from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from shopapp.models import Category, Manufacturer, Product


class CatalogTaxonomyStorefrontTests(TestCase):
    def setUp(self):
        self.electronics = Category.objects.create(
            name="Электроника",
            slug="electronics",
            is_featured=True,
            sort_index=1,
        )
        self.phones = Category.objects.create(
            name="Смартфоны",
            slug="phones",
            parent=self.electronics,
            sort_index=2,
        )
        self.appliances = Category.objects.create(
            name="Бытовая техника",
            slug="appliances",
            is_featured=True,
            sort_index=3,
        )
        self.brand_a = Manufacturer.objects.create(name="SkillPhone", slug="skillphone")
        self.brand_b = Manufacturer.objects.create(name="DjangoHome", slug="djangohome")

        self.phone = Product.objects.create(
            name="Смартфон SkillPhone X",
            short_description="Краткое описание смартфона",
            description="Полное описание смартфона",
            category=self.phones,
            manufacturer=self.brand_a,
            price=Decimal("50000.00"),
            sort_index=1,
            is_featured=True,
            is_limited_edition=True,
        )
        self.fridge = Product.objects.create(
            name="Холодильник DjangoHome",
            short_description="Краткое описание холодильника",
            description="Полное описание холодильника",
            category=self.appliances,
            manufacturer=self.brand_b,
            price=Decimal("70000.00"),
            sort_index=2,
        )

    def test_catalog_renders_categories_and_manufacturers_from_storefront(self):
        with override("ru"):
            response = self.client.get(reverse("shopapp:products_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Категории")
        self.assertContains(response, "Электроника")
        self.assertContains(response, "Смартфоны")
        self.assertContains(response, "SkillPhone")
        self.assertContains(response, "DjangoHome")

    def test_catalog_filters_by_child_category(self):
        with override("ru"):
            response = self.client.get(reverse("shopapp:products_list"), {"category": "phones"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.phone.name)
        self.assertNotContains(response, self.fridge.name)

    def test_catalog_filters_by_parent_category_with_children(self):
        with override("ru"):
            response = self.client.get(reverse("shopapp:products_list"), {"category": "electronics"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.phone.name)
        self.assertNotContains(response, self.fridge.name)

    def test_catalog_filters_by_manufacturer_and_search_query(self):
        with override("ru"):
            response = self.client.get(
                reverse("shopapp:products_list"),
                {
                    "manufacturer": str(self.brand_a.pk),
                    "q": "skillphone",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.phone.name)
        self.assertNotContains(response, self.fridge.name)

    def test_catalog_sorts_by_price_desc(self):
        with override("ru"):
            response = self.client.get(
                reverse("shopapp:products_list"),
                {
                    "sort": "price",
                    "direction": "desc",
                },
            )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode(response.charset or "utf-8")
        self.assertLess(
            content.index(self.fridge.name),
            content.index(self.phone.name),
        )

    def test_home_page_renders_featured_categories_and_limited_edition_products(self):
        with override("ru"):
            response = self.client.get(reverse("shopapp:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Популярные товары")
        self.assertContains(response, "Ограниченный тираж")
        self.assertContains(response, "Электроника")
        self.assertContains(response, self.phone.name)