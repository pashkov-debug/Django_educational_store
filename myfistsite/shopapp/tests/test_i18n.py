from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from shopapp.models import Order, Product


class ShopI18nConfigurationTests(TestCase):
    def test_product_and_order_model_names_are_localized(self):
        with override("en"):
            self.assertEqual(str(Product._meta.verbose_name), "product")
            self.assertEqual(str(Product._meta.verbose_name_plural), "products")
            self.assertEqual(str(Order._meta.verbose_name), "order")
            self.assertEqual(str(Order._meta.verbose_name_plural), "orders")

        with override("ru"):
            self.assertEqual(str(Product._meta.verbose_name), "товар")
            self.assertEqual(str(Product._meta.verbose_name_plural), "товары")
            self.assertEqual(str(Order._meta.verbose_name), "заказ")
            self.assertEqual(str(Order._meta.verbose_name_plural), "заказы")

    def test_product_detail_page_contains_english_labels(self):
        product = Product.objects.create(
            name="Локализованный товар",
            description="Описание для проверки переводов",
            price=Decimal("123.45"),
        )

        with override("en"):
            url = reverse("shopapp:product_detail", args=[product.pk])

        self.assertEqual(url, f"/en/catalog/{product.pk}/")

        response = self.client.get(url)

        self.assertContains(response, "Home")
        self.assertContains(response, "Products")
        self.assertContains(response, "Description")
        self.assertContains(response, "No related orders yet.")

    def test_product_detail_page_contains_russian_labels(self):
        product = Product.objects.create(
            name="Локализованный товар",
            description="Описание для проверки переводов",
            price=Decimal("123.45"),
        )

        with override("ru"):
            url = reverse("shopapp:product_detail", args=[product.pk])

        self.assertEqual(url, f"/ru/catalog/{product.pk}/")

        response = self.client.get(url)

        self.assertContains(response, "Главная")
        self.assertContains(response, "Товары")
        self.assertContains(response, "Описание")
        self.assertContains(response, "Связанных заказов пока нет.")
