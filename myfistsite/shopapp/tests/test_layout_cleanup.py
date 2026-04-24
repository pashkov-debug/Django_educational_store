from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from shopapp.models import Product


class LayoutCleanupTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="layout_cleanup_user",
            email="layout-cleanup@example.com",
            password="StrongPass123",
        )

    def test_about_page_uses_storefront_template(self):
        response = self.client.get(reverse("shopapp:layout_about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shopapp/storefront/about.html")
        self.assertContains(response, "О магазине")

    def test_sale_page_uses_storefront_template_and_shows_discount_products(self):
        sale_product = Product.objects.create(
            name="Товар со скидкой",
            description="Описание товара со скидкой",
            price=Decimal("1000.00"),
            discount=15,
        )
        regular_product = Product.objects.create(
            name="Товар без скидки",
            description="Описание товара без скидки",
            price=Decimal("1000.00"),
            discount=0,
        )

        response = self.client.get(reverse("shopapp:layout_sale"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shopapp/storefront/sale.html")
        self.assertContains(response, sale_product.name)
        self.assertNotContains(response, regular_product.name)

    def test_legacy_account_route_redirects_to_accounts_account(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("shopapp:layout_account"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:account"))

    def test_legacy_profile_route_redirects_to_accounts_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("shopapp:layout_profile"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:profile"))

    def test_legacy_profile_avatar_route_redirects_to_accounts_about_me(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("shopapp:layout_profile_avatar"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:about_me"))