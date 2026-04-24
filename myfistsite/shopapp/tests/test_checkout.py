from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from shopapp.checkout import CHECKOUT_SESSION_KEY
from shopapp.models import Cart, CartItem, Order, OrderItem, Product, ShopSettings


class CheckoutStorefrontTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Товар для оформления",
            short_description="Краткое описание товара",
            description="Описание товара",
            price=Decimal("1000.00"),
            discount=10,
        )
        ShopSettings.objects.update_or_create(
            pk=1,
            defaults={
                "regular_delivery_price": Decimal("200.00"),
                "free_delivery_threshold": Decimal("2000.00"),
                "express_delivery_price": Decimal("500.00"),
            },
        )

    def add_product_to_cart(self, quantity: int = 2):
        self.client.post(
            reverse("shopapp:cart_add", args=[self.product.pk]),
            data={"quantity": str(quantity)},
        )

    def test_empty_cart_redirects_to_cart_from_checkout(self):
        response = self.client.get(reverse("shopapp:checkout_customer"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("shopapp:layout_cart"))

    def test_customer_step_saves_data_to_session(self):
        self.add_product_to_cart()

        response = self.client.post(
            reverse("shopapp:checkout_customer"),
            data={
                "full_name": "Иван Покупатель",
                "email": "ivan@example.com",
                "phone": "+7 900 000 00 00",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("shopapp:checkout_delivery"))

        checkout_state = self.client.session[CHECKOUT_SESSION_KEY]
        self.assertEqual(checkout_state["customer"]["email"], "ivan@example.com")

    def test_delivery_step_calculates_regular_delivery_price(self):
        self.add_product_to_cart(quantity=1)

        session = self.client.session
        session[CHECKOUT_SESSION_KEY] = {
            "customer": {
                "full_name": "Иван Покупатель",
                "email": "ivan@example.com",
                "phone": "+7 900 000 00 00",
            }
        }
        session.save()

        response = self.client.post(
            reverse("shopapp:checkout_delivery"),
            data={
                "delivery_type": Order.DeliveryType.REGULAR,
                "city": "Москва",
                "address": "ул. Тестовая, дом 1",
            },
        )

        self.assertEqual(response.status_code, 302)
        checkout_state = self.client.session[CHECKOUT_SESSION_KEY]
        self.assertEqual(checkout_state["delivery"]["delivery_price"], "200.00")

    def test_confirm_creates_order_items_and_clears_cart(self):
        self.add_product_to_cart(quantity=2)

        session = self.client.session
        session[CHECKOUT_SESSION_KEY] = {
            "customer": {
                "full_name": "Иван Покупатель",
                "email": "ivan@example.com",
                "phone": "+7 900 000 00 00",
            },
            "delivery": {
                "delivery_type": Order.DeliveryType.EXPRESS,
                "city": "Москва",
                "address": "ул. Тестовая, дом 1",
                "delivery_price": "500.00",
            },
            "payment": {
                "payment_type": Order.PaymentType.CARD,
            },
        }
        session.save()

        response = self.client.post(
            reverse("shopapp:checkout_confirm"),
            data={"comment": "Позвонить перед доставкой"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("shopapp:layout_payment"))

        order = Order.objects.get(email="ivan@example.com")
        order_item = OrderItem.objects.get(order=order)

        self.assertEqual(order.full_name, "Иван Покупатель")
        self.assertEqual(order.delivery_type, Order.DeliveryType.EXPRESS)
        self.assertEqual(order.payment_type, Order.PaymentType.CARD)
        self.assertEqual(order.comment, "Позвонить перед доставкой")
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, Decimal("900.00"))
        self.assertEqual(order_item.total_price, Decimal("1800.00"))
        self.assertEqual(order.total_price_snapshot, Decimal("2300.00"))

        cart = Cart.objects.get(session_key=self.client.session.session_key, user__isnull=True)
        self.assertEqual(cart.items.count(), 0)
        self.assertNotIn(CHECKOUT_SESSION_KEY, self.client.session)

    def test_checkout_pages_render_russian_labels(self):
        self.add_product_to_cart()

        with override("ru"):
            response = self.client.get(reverse("shopapp:checkout_customer"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Оформление заказа")
        self.assertContains(response, "Ф. И. О.")
        self.assertContains(response, "Дальше")