
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def seed_storefront(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Category = apps.get_model("shopapp", "Category")
    Product = apps.get_model("shopapp", "Product")
    ShopSettings = apps.get_model("shopapp", "ShopSettings")


    admin_user, admin_created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@example.com",
            "is_staff": True,
            "is_superuser": True,
            "password": make_password("123456"),
        },
    )
    if not admin_created:
        changed = False
        if not admin_user.is_staff:
            admin_user.is_staff = True
            changed = True
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            changed = True
        if changed:
            admin_user.save(update_fields=["is_staff", "is_superuser"])

    for username, email in [("buyer1", "buyer1@example.com"), ("buyer2", "buyer2@example.com")]:
        User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "password": make_password("123456"),
            },
        )

    electronics, _ = Category.objects.get_or_create(
        title="Electronics",
        defaults={
            "slug": "electronics",
            "icon": "/static/frontend/assets/img/icons/departments/1.svg",
            "sort_index": 10,
        },
    )
    accessories, _ = Category.objects.get_or_create(
        title="Accessories",
        defaults={
            "slug": "accessories",
            "icon": "/static/frontend/assets/img/icons/departments/2.svg",
            "sort_index": 20,
        },
    )


    if not Product.objects.exists():
        demo_products = [
            {
                "name": "Wireless Headphones",
                "description": "Comfortable wireless headphones with clear sound and long battery life.",
                "price": 129.99,
                "discount": 15,
                "manufacturer": "Megano",
                "limited_edition": True,
                "category_id": electronics.pk,
                "short_description": "Wireless over-ear headphones",
            },
            {
                "name": "Gaming Mouse",
                "description": "Ergonomic gaming mouse with high precision sensor and RGB backlight.",
                "price": 59.90,
                "discount": 10,
                "manufacturer": "Megano",
                "limited_edition": True,
                "category_id": accessories.pk,
                "short_description": "Precision RGB mouse",
            },
            {
                "name": "4K Monitor",
                "description": "Ultra HD monitor for work and entertainment with vivid colors and sharp details.",
                "price": 399.00,
                "discount": 5,
                "manufacturer": "Megano",
                "limited_edition": False,
                "category_id": electronics.pk,
                "short_description": "27-inch 4K display",
            },
            {
                "name": "Mechanical Keyboard",
                "description": "Mechanical keyboard with tactile switches and compact layout.",
                "price": 89.50,
                "discount": 20,
                "manufacturer": "Megano",
                "limited_edition": False,
                "category_id": accessories.pk,
                "short_description": "Compact mechanical keyboard",
            },
        ]
        for index, data in enumerate(demo_products, start=1):
            Product.objects.create(
                sort_index=index,
                in_stock=True,
                created_by=admin_user,
                **data,
            )

    products = list(Product.objects.all().order_by("pk"))
    for index, product in enumerate(products, start=1):
        product.category_id = electronics.pk if index % 2 else accessories.pk
        product.short_description = product.short_description or (product.description[:120] if product.description else product.name)
        product.manufacturer = product.manufacturer or "Megano"
        product.sort_index = index
        product.in_stock = True
        product.limited_edition = index <= 4
        product.save(
            update_fields=[
                "category",
                "short_description",
                "manufacturer",
                "sort_index",
                "in_stock",
                "limited_edition",
            ]
        )

    ShopSettings.objects.get_or_create(
        pk=1,
        defaults={
            "singleton_key": 1,
            "free_delivery_threshold": 2000,
            "delivery_cost": 200,
            "express_delivery_cost": 500,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0011_alter_order_options_alter_product_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=150, unique=True)),
                ("icon", models.CharField(blank=True, default="", max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_index", models.PositiveIntegerField(default=0)),
                ("archived", models.BooleanField(default=False)),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="children", to="shopapp.category")),
            ],
            options={
                "ordering": ("sort_index", "title"),
                "verbose_name": "category",
                "verbose_name_plural": "categories",
            },
        ),
        migrations.AddField(
            model_name="product",
            name="category",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="shopapp.category"),
        ),
        migrations.AddField(
            model_name="product",
            name="in_stock",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="product",
            name="limited_edition",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="product",
            name="manufacturer",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="product",
            name="short_description",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="sort_index",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="order",
            name="address",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="order",
            name="city",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="order",
            name="comment",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_type",
            field=models.CharField(blank=True, choices=[("delivery", "Delivery"), ("express", "Express delivery")], default="delivery", max_length=32),
        ),
        migrations.AddField(
            model_name="order",
            name="email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="order",
            name="full_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_attempted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_error",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_number",
            field=models.CharField(blank=True, default="", max_length=8),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_type",
            field=models.CharField(blank=True, choices=[("card", "Online card"), ("random_account", "Online from random account")], default="card", max_length=32),
        ),
        migrations.AddField(
            model_name="order",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(choices=[("draft", "Draft"), ("new", "New"), ("paid", "Paid"), ("payment_error", "Payment error")], default="draft", max_length=32),
        ),
        migrations.CreateModel(
            name="ShopSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("singleton_key", models.PositiveSmallIntegerField(default=1, editable=False, unique=True)),
                ("free_delivery_threshold", models.DecimalField(decimal_places=2, default=2000, max_digits=10)),
                ("delivery_cost", models.DecimalField(decimal_places=2, default=200, max_digits=10)),
                ("express_delivery_cost", models.DecimalField(decimal_places=2, default=500, max_digits=10)),
            ],
            options={
                "verbose_name": "shop settings",
                "verbose_name_plural": "shop settings",
            },
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author", models.CharField(max_length=255)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("text", models.TextField()),
                ("rate", models.PositiveSmallIntegerField(default=5)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="shopapp.product")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
                "verbose_name": "review",
                "verbose_name_plural": "reviews",
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("price_snapshot", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="shopapp.order")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="shopapp.product")),
            ],
            options={
                "ordering": ("pk",),
                "verbose_name": "order item",
                "verbose_name_plural": "order items",
                "unique_together": {("order", "product")},
            },
        ),
        migrations.RunPython(seed_storefront, migrations.RunPython.noop),
    ]
