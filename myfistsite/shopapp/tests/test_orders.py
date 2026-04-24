from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from shopapp.forms import OrderForm
from shopapp.models import Order, Product
from shopapp.views import OrderDetailView, orders_export_view


class OrderBusinessLogicTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="buyer1",
            email="buyer1@example.com",
            password="123456Test",
        )
        self.product_1 = Product.objects.create(
            name="Товар 1",
            description="Первый товар",
            price=Decimal("1000.00"),
            discount=10,
        )
        self.product_2 = Product.objects.create(
            name="Товар 2",
            description="Второй товар",
            price=Decimal("500.00"),
        )

    def test_order_total_price_sums_discounted_products(self):
        order = Order.objects.create(
            user=self.user,
            delivery_address="Москва, ул. Примерная, дом 1",
        )
        order.products.add(self.product_1, self.product_2)

        self.assertEqual(order.total_price, Decimal("1400.00"))
        self.assertEqual(order.products_count, 2)

    def test_order_form_requires_products_and_full_address(self):
        form = OrderForm(
            data={
                "delivery_address": "Коротко",
                "promo_code": "SALE10",
                "status": "new",
                "user": self.user.pk,
                "products": [],
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Укажите более полный адрес доставки.", form.errors["delivery_address"])
        self.assertIn("Выберите хотя бы один товар.", form.errors["products"])

    def test_order_list_shows_user_and_product(self):
        order = Order.objects.create(
            user=self.user,
            delivery_address="Санкт-Петербург, Невский проспект, дом 10",
        )
        order.products.add(self.product_1)

        response = self.client.get(reverse("shopapp:orders"))

        self.assertContains(response, self.user.username)
        self.assertContains(response, self.product_1.name)
        self.assertTemplateUsed(response, "shopapp/storefront/orders.html")
        self.assertEqual(response.context["orders"][0].pk, order.pk)


class OrderDetailViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create_user(
            username="order_viewer",
            email="order_viewer@example.com",
            password="StrongPass123",
        )
        cls.user.user_permissions.add(Permission.objects.get(codename="view_order"))

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        super().tearDownClass()

    def setUp(self):
        self.client.force_login(self.user)
        self.product = Product.objects.create(
            name="Товар для детального заказа",
            description="Товар для проверки detail-view",
            price=Decimal("999.00"),
        )
        self.order = Order.objects.create(
            user=self.user,
            delivery_address="Москва, ул. Тестовая, дом 42",
            promo_code="SPRING42",
        )
        self.order.products.add(self.product)

    def tearDown(self):
        self.order.delete()

    def test_order_details(self):
        response = self.client.get(reverse("shopapp:order_detail", kwargs={"pk": self.order.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertIs(response.resolver_match.func.view_class, OrderDetailView)
        self.assertTemplateUsed(response, "shopapp/storefront/order_detail.html")
        self.assertContains(response, self.order.delivery_address)
        self.assertContains(response, self.order.promo_code)
        self.assertEqual(response.context["order"].pk, self.order.pk)


class OrdersExportTestCase(TestCase):
    fixtures = ["users.json", "products.json", "orders.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.staff_user = get_user_model().objects.create_user(
            username="export_staff",
            email="export_staff@example.com",
            password="StrongPass123",
            is_staff=True,
        )
        cls.non_staff_user = get_user_model().objects.create_user(
            username="export_non_staff",
            email="export_non_staff@example.com",
            password="StrongPass123",
            is_staff=False,
        )

    @classmethod
    def tearDownClass(cls):
        cls.staff_user.delete()
        cls.non_staff_user.delete()
        super().tearDownClass()

    def _build_expected_payload(self):
        orders = (
            Order.objects.select_related("user")
            .prefetch_related("products")
            .order_by("pk")
        )
        return {
            "orders": [
                {
                    "id": order.pk,
                    "delivery_address": order.delivery_address,
                    "promo_code": order.promo_code,
                    "user_id": order.user_id,
                    "product_ids": list(order.products.values_list("pk", flat=True)),
                }
                for order in orders
            ]
        }

    def test_orders_export_available_for_staff_user(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("shopapp:orders_export"))

        self.assertEqual(response.status_code, 200)
        self.assertIs(response.resolver_match.func, orders_export_view)
        self.assertEqual(response.json(), self._build_expected_payload())

    def test_orders_export_denies_access_for_non_staff_user(self):
        self.client.force_login(self.non_staff_user)

        response = self.client.get(reverse("shopapp:orders_export"))

        self.assertRedirects(
            response,
            f'{reverse("accounts:login")}?next={reverse("shopapp:orders_export")}',
            fetch_redirect_response=False,
        )
