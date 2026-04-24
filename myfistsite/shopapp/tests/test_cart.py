from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from shopapp.models import Cart, CartItem, Product


class CartStorefrontTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Товар для корзины",
            short_description="Краткое описание товара для корзины",
            description="Полное описание товара для корзины",
            price=Decimal("1000.00"),
            discount=10,
        )

    def assert_response_contains_any(self, response, expected_values: tuple[str, ...]) -> None:
        content = response.content.decode(response.charset or "utf-8")

        self.assertTrue(
            any(value in content for value in expected_values),
            msg=f"Response does not contain any of: {expected_values}",
        )

    def test_guest_can_add_product_to_cart(self):
        response = self.client.post(
            reverse("shopapp:cart_add", args=[self.product.pk]),
            data={"quantity": "2"},
        )

        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(session_key=self.client.session.session_key, user__isnull=True)
        item = CartItem.objects.get(cart=cart, product=self.product)

        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price_snapshot, Decimal("900.00"))

    def test_cart_accepts_discount_price_with_extra_decimal_places(self):
        product = Product.objects.create(
            name="Портативная колонка SkillPhone Sound",
            short_description="Краткое описание",
            description="Описание",
            price=Decimal("5990.00"),
            discount=12,
        )

        response = self.client.post(
            reverse("shopapp:cart_add", args=[product.pk]),
            data={"quantity": "1"},
        )

        self.assertEqual(response.status_code, 302)

        item = CartItem.objects.get(product=product)

        self.assertEqual(item.price_snapshot, Decimal("5271.20"))

    def test_cart_page_shows_added_product(self):
        self.client.post(
            reverse("shopapp:cart_add", args=[self.product.pk]),
            data={"quantity": "1"},
        )

        with override("ru"):
            response = self.client.get(reverse("shopapp:layout_cart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Корзина")
        self.assertContains(response, self.product.name)
        self.assert_response_contains_any(response, ("₽900,00", "₽900.00"))

    def test_cart_item_quantity_can_be_updated(self):
        self.client.post(
            reverse("shopapp:cart_add", args=[self.product.pk]),
            data={"quantity": "1"},
        )

        item = CartItem.objects.get(product=self.product)

        response = self.client.post(
            reverse("shopapp:cart_item_update", args=[item.pk]),
            data={"quantity": "4"},
        )

        self.assertEqual(response.status_code, 302)

        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)

    def test_cart_item_can_be_deleted(self):
        self.client.post(
            reverse("shopapp:cart_add", args=[self.product.pk]),
            data={"quantity": "1"},
        )

        item = CartItem.objects.get(product=self.product)

        response = self.client.post(reverse("shopapp:cart_item_delete", args=[item.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_cart_total_price_is_calculated(self):
        self.client.post(
            reverse("shopapp:cart_add", args=[self.product.pk]),
            data={"quantity": "3"},
        )

        cart = Cart.objects.get(session_key=self.client.session.session_key, user__isnull=True)

        self.assertEqual(cart.total_quantity, 3)
        self.assertEqual(cart.total_price, Decimal("2700.00"))

    def test_authenticated_user_gets_user_cart(self):
        user = get_user_model().objects.create_user(
            username="cart_user",
            email="cart_user@example.com",
            password="StrongPass123",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("shopapp:cart_add", args=[self.product.pk]),
            data={"quantity": "2"},
        )

        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(user=user, is_active=True)
        self.assertEqual(cart.total_quantity, 2)

    def test_cart_counter_is_visible_in_storefront_header(self):
        self.client.post(
            reverse("shopapp:cart_add", args=[self.product.pk]),
            data={"quantity": "3"},
        )

        response = self.client.get(reverse("shopapp:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="CartBlock-amount">3</span>', html=True)