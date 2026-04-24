from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from shopapp.models import Order, Product


class ShopI18nConfigurationTests(TestCase):
    def assert_response_contains_any(self, response, expected_values: tuple[str, ...]) -> None:
        content = response.content.decode(response.charset or "utf-8")

        self.assertTrue(
            any(value in content for value in expected_values),
            msg=f"Response does not contain any of: {expected_values}",
        )

    def create_product(self) -> Product:
        return Product.objects.create(
            name="Локализованный товар",
            description="Описание для проверки переводов",
            price=Decimal("123.45"),
        )

    def test_product_and_order_model_names_are_configured(self):
        with override("en"):
            self.assertIn(str(Product._meta.verbose_name), {"product", "товар"})
            self.assertIn(str(Product._meta.verbose_name_plural), {"products", "товары"})
            self.assertIn(str(Order._meta.verbose_name), {"order", "заказ"})
            self.assertIn(str(Order._meta.verbose_name_plural), {"orders", "заказы"})

        with override("ru"):
            self.assertIn(str(Product._meta.verbose_name), {"product", "товар"})
            self.assertIn(str(Product._meta.verbose_name_plural), {"products", "товары"})
            self.assertIn(str(Order._meta.verbose_name), {"order", "заказ"})
            self.assertIn(str(Order._meta.verbose_name_plural), {"orders", "заказы"})

    def test_product_detail_page_is_available_with_english_prefix(self):
        product = self.create_product()

        with override("en"):
            url = reverse("shopapp:product_detail", args=[product.pk])

        self.assertEqual(url, f"/en/catalog/{product.pk}/")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)
        self.assertContains(response, product.description)
        self.assert_response_contains_any(response, ("Home", "Главная"))
        self.assert_response_contains_any(response, ("Products", "Товары"))
        self.assert_response_contains_any(response, ("Description", "Описание"))
        self.assert_response_contains_any(
            response,
            (
                "No related orders yet.",
                "Связанных заказов пока нет.",
            ),
        )

    def test_product_detail_page_is_available_with_russian_prefix(self):
        product = self.create_product()

        with override("ru"):
            url = reverse("shopapp:product_detail", args=[product.pk])

        self.assertEqual(url, f"/ru/catalog/{product.pk}/")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)
        self.assertContains(response, product.description)
        self.assert_response_contains_any(response, ("Home", "Главная"))
        self.assert_response_contains_any(response, ("Products", "Товары"))
        self.assert_response_contains_any(response, ("Description", "Описание"))
        self.assert_response_contains_any(
            response,
            (
                "No related orders yet.",
                "Связанных заказов пока нет.",
            ),
        )