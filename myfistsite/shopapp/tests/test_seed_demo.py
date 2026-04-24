from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from shopapp.models import Category, Manufacturer, Order, Product


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_creates_storefront_data(self):
        call_command("seed_demo", verbosity=0)

        self.assertTrue(Group.objects.filter(name="Покупатель").exists())
        self.assertTrue(Group.objects.filter(name="Администратор").exists())

        user_model = get_user_model()

        admin = user_model.objects.get(username="admin_demo")
        buyer = user_model.objects.get(username="buyer_demo_1")

        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("admin123456"))
        self.assertTrue(buyer.check_password("123456"))

        self.assertGreaterEqual(Category.objects.count(), 9)
        self.assertGreaterEqual(Manufacturer.objects.count(), 4)
        self.assertGreaterEqual(Product.objects.count(), 10)
        self.assertGreaterEqual(Order.objects.count(), 4)

        self.assertTrue(Category.objects.filter(slug="electronics", is_featured=True).exists())
        self.assertTrue(Product.objects.filter(is_limited_edition=True).exists())
        self.assertTrue(Order.objects.filter(promo_code="DEMO-ORDER-001").exists())

    def test_seed_demo_is_idempotent(self):
        call_command("seed_demo", verbosity=0)

        counts_after_first_run = {
            "categories": Category.objects.count(),
            "manufacturers": Manufacturer.objects.count(),
            "products": Product.objects.count(),
            "orders": Order.objects.count(),
        }

        call_command("seed_demo", verbosity=0)

        self.assertEqual(Category.objects.count(), counts_after_first_run["categories"])
        self.assertEqual(Manufacturer.objects.count(), counts_after_first_run["manufacturers"])
        self.assertEqual(Product.objects.count(), counts_after_first_run["products"])
        self.assertEqual(Order.objects.count(), counts_after_first_run["orders"])

    def test_seed_demo_reset_rebuilds_data(self):
        call_command("seed_demo", verbosity=0)

        Product.objects.create(
            name="Не демо товар",
            description="Этот товар не должен удаляться reset-командой.",
            price="100.00",
        )

        call_command("seed_demo", "--reset", verbosity=0)

        self.assertTrue(Product.objects.filter(name="Не демо товар").exists())
        self.assertTrue(Product.objects.filter(name="Смартфон SkillPhone X").exists())
        self.assertTrue(Category.objects.filter(slug="smartphones").exists())