from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from shopapp.models import Order, OrderItem, Payment, Product


class PaymentStorefrontTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="payment_user",
            email="payment@example.com",
            password="StrongPass123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other_payment_user",
            email="other-payment@example.com",
            password="StrongPass123",
        )
        self.product = Product.objects.create(
            name="Товар для оплаты",
            description="Описание товара для оплаты",
            price=Decimal("1000.00"),
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name="Иван Покупатель",
            email="payment@example.com",
            phone="+7 900 000 00 00",
            city="Москва",
            address="ул. Тестовая, дом 1",
            delivery_address="Москва, ул. Тестовая, дом 1",
            delivery_price=Decimal("200.00"),
            total_price_snapshot=Decimal("1200.00"),
            payment_status=Order.PaymentStatus.NOT_STARTED,
            payment_type=Order.PaymentType.CARD,
            status="new",
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name_snapshot=self.product.name,
            quantity=1,
            unit_price=Decimal("1000.00"),
            total_price=Decimal("1000.00"),
        )

    def test_payment_page_renders_order(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("shopapp:layout_payment"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Заказ №{self.order.pk}")
        self.assertContains(response, "Итого к оплате")

    def test_payment_submit_creates_pending_payment(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("shopapp:layout_payment"),
            data={"account_number": "22222222"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("shopapp:layout_progress_payment"))

        payment = Payment.objects.get(order=self.order)

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.account_number, "22222222")

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_process_payments_marks_successful_payment_paid(self):
        Payment.objects.create(
            order=self.order,
            account_number="22222222",
            amount=self.order.total_price,
            status=Payment.Status.PENDING,
        )
        self.order.payment_status = Order.PaymentStatus.PENDING
        self.order.save(update_fields=("payment_status",))

        call_command("process_payments", verbosity=0)

        payment = Payment.objects.get(order=self.order)

        payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.status, "paid")

    def test_process_payments_marks_number_ending_with_zero_failed(self):
        Payment.objects.create(
            order=self.order,
            account_number="22222220",
            amount=self.order.total_price,
            status=Payment.Status.PENDING,
        )
        self.order.payment_status = Order.PaymentStatus.PENDING
        self.order.save(update_fields=("payment_status",))

        call_command("process_payments", verbosity=0)

        payment = Payment.objects.get(order=self.order)

        payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(payment.status, Payment.Status.FAILED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(self.order.status, "payment_failed")
        self.assertTrue(self.order.payment_error)

    def test_process_payments_marks_odd_number_failed(self):
        Payment.objects.create(
            order=self.order,
            account_number="11111111",
            amount=self.order.total_price,
            status=Payment.Status.PENDING,
        )
        self.order.payment_status = Order.PaymentStatus.PENDING
        self.order.save(update_fields=("payment_status",))

        call_command("process_payments", verbosity=0)

        payment = Payment.objects.get(order=self.order)

        payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(payment.status, Payment.Status.FAILED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)

    def test_progress_page_shows_payment_status(self):
        self.client.force_login(self.user)
        payment = Payment.objects.create(
            order=self.order,
            account_number="22222222",
            amount=self.order.total_price,
            status=Payment.Status.PENDING,
        )
        session = self.client.session
        session["payment_id"] = payment.pk
        session["payment_order_id"] = self.order.pk
        session.save()

        response = self.client.get(reverse("shopapp:layout_progress_payment"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Платёж №{payment.pk}")
        self.assertContains(response, "Ожидает обработки")

    def test_payment_someone_creates_pending_payment(self):
        self.client.force_login(self.user)
        self.order.payment_type = Order.PaymentType.RANDOM_ACCOUNT
        self.order.save(update_fields=("payment_type",))

        response = self.client.post(reverse("shopapp:layout_payment_someone"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("shopapp:layout_progress_payment"))

        payment = Payment.objects.get(order=self.order)

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(len(payment.account_number), 8)
        self.assertTrue(payment.account_number.isdigit())

    def test_order_detail_forbidden_for_not_owner(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("shopapp:order_detail", args=[self.order.pk]))

        self.assertEqual(response.status_code, 403)