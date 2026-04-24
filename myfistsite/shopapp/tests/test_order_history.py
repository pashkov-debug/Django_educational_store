from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from shopapp.models import Order, OrderItem, Product


class UserOrderHistoryTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.user = user_model.objects.create_user(
            username="history_user",
            email="history@example.com",
            password="StrongPass123",
        )
        self.other_user = user_model.objects.create_user(
            username="other_history_user",
            email="other-history@example.com",
            password="StrongPass123",
        )

        self.product = Product.objects.create(
            name="Товар истории заказов",
            description="Описание товара истории заказов",
            price=Decimal("1000.00"),
        )

        self.user_order = Order.objects.create(
            user=self.user,
            full_name="Иван История",
            email="history@example.com",
            phone="+7 900 000 00 00",
            city="Москва",
            address="ул. Истории, дом 1",
            delivery_address="Москва, ул. Истории, дом 1",
            delivery_price=Decimal("200.00"),
            total_price_snapshot=Decimal("1200.00"),
            payment_status=Order.PaymentStatus.FAILED,
            payment_type=Order.PaymentType.CARD,
            status="payment_failed",
        )
        OrderItem.objects.create(
            order=self.user_order,
            product=self.product,
            product_name_snapshot=self.product.name,
            quantity=1,
            unit_price=Decimal("1000.00"),
            total_price=Decimal("1000.00"),
        )

        self.other_order = Order.objects.create(
            user=self.other_user,
            full_name="Чужой Пользователь",
            email="other-history@example.com",
            phone="+7 900 000 00 01",
            city="Казань",
            address="ул. Чужая, дом 1",
            delivery_address="Казань, ул. Чужая, дом 1",
            delivery_price=Decimal("200.00"),
            total_price_snapshot=Decimal("1200.00"),
            payment_status=Order.PaymentStatus.NOT_STARTED,
            payment_type=Order.PaymentType.CARD,
            status="new",
        )

    def test_history_order_requires_login(self):
        response = self.client.get(reverse("shopapp:layout_history_order"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_history_order_shows_only_current_user_orders(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("shopapp:layout_history_order"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Заказ №{self.user_order.pk}")
        self.assertContains(response, "История заказов")
        self.assertContains(response, "Оплатить")
        self.assertNotContains(response, f"Заказ №{self.other_order.pk}")

    def test_order_detail_contains_order_items_and_payment_status(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("shopapp:order_detail", args=[self.user_order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, "Статус оплаты")
        self.assertContains(response, "Ошибка оплаты")
        self.assertContains(response, "Оплатить")