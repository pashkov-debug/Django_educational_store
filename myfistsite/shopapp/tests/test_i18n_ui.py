from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from shopapp.models import Product


class StorefrontI18nUiTests(TestCase):
    def test_about_page_has_russian_interface(self):
        with override("ru"):
            response = self.client.get(reverse("shopapp:layout_about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "О магазине")
        self.assertContains(response, "Почему выбирают наш магазин")

    def test_about_page_has_english_interface(self):
        with override("en"):
            response = self.client.get(reverse("shopapp:layout_about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About")
        self.assertContains(response, "Why choose our store")

    def test_sale_page_has_english_interface_without_translating_product_name(self):
        product = Product.objects.create(
            name="Товар со скидкой",
            description="Описание товара",
            price=Decimal("1000.00"),
            discount=10,
        )

        with override("en"):
            response = self.client.get(reverse("shopapp:layout_sale"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Discounts")
        self.assertContains(response, product.name)

    def test_login_page_has_english_interface(self):
        with override("en"):
            response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in to account")
