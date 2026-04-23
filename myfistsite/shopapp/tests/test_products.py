from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from shopapp.forms import ProductForm
from shopapp.models import Product


class ProductBusinessLogicTests(TestCase):
    def test_product_final_price_respects_discount(self):
        product = Product.objects.create(
            name="Игровая мышь",
            description="Лёгкая мышь для шутеров",
            price=Decimal("2000.00"),
            discount=25,
        )

        self.assertEqual(product.final_price, Decimal("1500.00"))
        self.assertTrue(product.has_discount)

    def test_catalog_shows_only_not_archived_products(self):
        Product.objects.create(
            name="Активный товар",
            description="Доступен в каталоге",
            price=Decimal("100.00"),
            archived=False,
        )
        Product.objects.create(
            name="Архивный товар",
            description="Скрыт из каталога",
            price=Decimal("200.00"),
            archived=True,
        )

        response = self.client.get(reverse("shopapp:catalog"))

        self.assertContains(response, "Активный товар")
        self.assertNotContains(response, "Архивный товар")
        self.assertTemplateUsed(response, "shopapp/storefront/catalog.html")

    def test_product_archive_marks_product_as_archived_without_deleting(self):
        admin = get_user_model().objects.create_superuser(
            username="admin_archive",
            email="admin_archive@example.com",
            password="StrongPass123",
        )
        self.client.force_login(admin)

        product = Product.objects.create(
            name="Товар в архив",
            description="Будет архивирован",
            price=Decimal("300.00"),
            archived=False,
        )

        response = self.client.post(reverse("shopapp:product_archive", args=[product.pk]))

        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertTrue(product.archived)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_product_form_rejects_non_positive_price(self):
        form = ProductForm(
            data={
                "name": "Ошибка цены",
                "description": "Проверка валидации",
                "price": "0",
                "discount": "5",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Цена должна быть больше нуля.", form.errors["price"])


class ProductPracticePermissionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.author = user_model.objects.create_user(
            username="author",
            email="author@example.com",
            password="StrongPass123",
        )
        self.other_user = user_model.objects.create_user(
            username="other_user",
            email="other_user@example.com",
            password="StrongPass123",
        )
        self.superuser = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="StrongPass123",
        )

        self.add_permission = Permission.objects.get(codename="add_product")
        self.change_permission = Permission.objects.get(codename="change_product")

        self.product = Product.objects.create(
            name="Тестовый товар",
            description="Описание товара",
            price=Decimal("1000.00"),
            discount=10,
            created_by=self.author,
        )

    def test_create_page_requires_add_permission(self):
        self.client.force_login(self.author)

        response = self.client.get(reverse("shopapp:product_create"))

        self.assertEqual(response.status_code, 403)

    def test_create_page_available_with_add_permission(self):
        self.author.user_permissions.add(self.add_permission)
        self.client.force_login(self.author)

        response = self.client.get(reverse("shopapp:product_create"))

        self.assertTemplateUsed(response, "shopapp/storefront/product_form.html")
        self.assertIn("form", response.context)

    def test_create_product_sets_created_by_current_user(self):
        self.author.user_permissions.add(self.add_permission)
        self.client.force_login(self.author)

        response = self.client.post(
            reverse("shopapp:product_create"),
            data={
                "name": "Новый товар",
                "description": "Описание нового товара",
                "price": "1999.99",
                "discount": "5",
            },
        )

        self.assertEqual(response.status_code, 302)
        created_product = Product.objects.get(name="Новый товар")
        self.assertEqual(created_product.created_by, self.author)

    def test_catalog_hides_create_link_without_permission(self):
        self.client.force_login(self.author)

        response = self.client.get(reverse("shopapp:catalog"))

        self.assertNotContains(response, reverse("shopapp:product_create"))

    def test_catalog_shows_create_link_with_permission(self):
        self.author.user_permissions.add(self.add_permission)
        self.client.force_login(self.author)

        response = self.client.get(reverse("shopapp:catalog"))

        self.assertContains(response, reverse("shopapp:product_create"))

    def test_superuser_can_edit_any_product(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("shopapp:product_update", kwargs={"pk": self.product.pk})
        )

        self.assertTemplateUsed(response, "shopapp/storefront/product_form.html")
        self.assertEqual(response.context["product"].pk, self.product.pk)

    def test_author_with_change_permission_can_edit_own_product(self):
        self.author.user_permissions.add(self.change_permission)
        self.client.force_login(self.author)

        response = self.client.get(
            reverse("shopapp:product_update", kwargs={"pk": self.product.pk})
        )

        self.assertTemplateUsed(response, "shopapp/storefront/product_form.html")
        self.assertEqual(response.context["product"].pk, self.product.pk)

    def test_author_without_change_permission_cannot_edit_own_product(self):
        self.client.force_login(self.author)

        response = self.client.get(
            reverse("shopapp:product_update", kwargs={"pk": self.product.pk})
        )

        self.assertEqual(response.status_code, 403)

    def test_user_with_change_permission_cannot_edit_foreign_product(self):
        self.other_user.user_permissions.add(self.change_permission)
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("shopapp:product_update", kwargs={"pk": self.product.pk})
        )

        self.assertEqual(response.status_code, 403)
