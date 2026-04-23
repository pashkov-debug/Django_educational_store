from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from shopapp.models import Order, Product


class ProductApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="api_buyer",
            email="api_buyer@example.com",
            password="StrongPass123",
        )
        self.mouse = Product.objects.create(
            name="Игровая мышь",
            description="Лёгкая мышь для шутеров",
            price=Decimal("3000.00"),
            discount=10,
        )
        self.keyboard = Product.objects.create(
            name="Игровая клавиатура",
            description="Механическая клавиатура",
            price=Decimal("5000.00"),
        )
        self.archived_product = Product.objects.create(
            name="Архивный товар",
            description="Не должен попадать в API",
            price=Decimal("1000.00"),
            archived=True,
        )

        first_order = Order.objects.create(
            user=self.user,
            delivery_address="Москва, ул. Тестовая, дом 1",
        )
        first_order.products.add(self.mouse)

        second_order = Order.objects.create(
            user=self.user,
            delivery_address="Москва, ул. Тестовая, дом 2",
        )
        second_order.products.add(self.mouse)

        third_order = Order.objects.create(
            user=self.user,
            delivery_address="Москва, ул. Тестовая, дом 3",
        )
        third_order.products.add(self.keyboard)

    def test_products_api_supports_search_and_ordering(self):
        response = self.client.get(
            reverse("shopapp:product-list"),
            {"search": "мышь", "ordering": "-purchases_count"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.mouse.pk)
        self.assertEqual(response.data["results"][0]["purchases_count"], 2)

    def test_anonymous_user_cannot_create_product(self):
        response = self.client.post(
            reverse("shopapp:product-list"),
            {
                "name": "Новый товар",
                "description": "Описание нового товара",
                "price": "1500.00",
                "discount": 0,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_delete_archives_entity_instead_of_hard_delete(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(reverse("shopapp:product-detail", args=[self.keyboard.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.keyboard.refresh_from_db()
        self.assertTrue(self.keyboard.archived)
        self.assertTrue(Product.objects.filter(pk=self.keyboard.pk).exists())


class OrderApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="orders_user",
            email="orders_user@example.com",
            password="StrongPass123",
        )
        self.other_user = user_model.objects.create_user(
            username="other_orders_user",
            email="other_orders_user@example.com",
            password="StrongPass123",
        )
        self.product = Product.objects.create(
            name="Смартфон",
            description="Товар для заказа",
            price=Decimal("12000.00"),
        )

        self.old_paid_order = Order.objects.create(
            user=self.user,
            delivery_address="Казань, ул. Старая, дом 5",
            status="paid",
            promo_code="SPRING",
        )
        self.old_paid_order.products.add(self.product)
        Order.objects.filter(pk=self.old_paid_order.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )

        self.new_paid_order = Order.objects.create(
            user=self.user,
            delivery_address="Казань, ул. Новая, дом 7",
            status="paid",
            promo_code="SPRING",
        )
        self.new_paid_order.products.add(self.product)

        self.foreign_new_order = Order.objects.create(
            user=self.other_user,
            delivery_address="Самара, ул. Центральная, дом 10",
            status="new",
        )
        self.foreign_new_order.products.add(self.product)

    def test_orders_api_supports_filtering_and_ordering(self):
        response = self.client.get(
            reverse("shopapp:order-list"),
            {
                "status": "paid",
                "user": self.user.pk,
                "ordering": "created_at",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        ordered_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ordered_ids, [self.old_paid_order.pk, self.new_paid_order.pk])

    def test_anonymous_user_cannot_create_order(self):
        response = self.client.post(
            reverse("shopapp:order-list"),
            {
                "delivery_address": "Москва, ул. Полная, дом 10",
                "promo_code": "SALE10",
                "status": "new",
                "user": self.user.pk,
                "products": [self.product.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_orders_api_rejects_creation_without_products(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("shopapp:order-list"),
            {
                "delivery_address": "Москва, ул. Полная, дом 10",
                "promo_code": "SALE10",
                "status": "new",
                "user": self.user.pk,
                "products": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("products", response.data)

    def test_order_delete_archives_entity_instead_of_hard_delete(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(reverse("shopapp:order-detail", args=[self.new_paid_order.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.new_paid_order.refresh_from_db()
        self.assertTrue(self.new_paid_order.archived)
        self.assertTrue(Order.objects.filter(pk=self.new_paid_order.pk).exists())
