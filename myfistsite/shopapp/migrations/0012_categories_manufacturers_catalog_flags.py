# Generated for storefront catalog step.

import django.db.models.deletion
import shopapp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0011_alter_order_options_alter_product_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="Название")),
                ("slug", models.SlugField(allow_unicode=True, blank=True, max_length=140, unique=True, verbose_name="Слаг")),
                ("icon", models.ImageField(blank=True, upload_to=shopapp.models.category_icon_upload_to, verbose_name="Иконка")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("is_featured", models.BooleanField(default=False, verbose_name="Избранная на главной")),
                ("sort_index", models.PositiveIntegerField(default=100, verbose_name="Индекс сортировки")),
                ("archived", models.BooleanField(default=False, verbose_name="В архиве")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлена")),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="children",
                        to="shopapp.category",
                        verbose_name="Родительская категория",
                    ),
                ),
            ],
            options={
                "verbose_name": "категория",
                "verbose_name_plural": "категории",
                "ordering": ("sort_index", "name"),
            },
        ),
        migrations.CreateModel(
            name="Manufacturer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="Название")),
                ("slug", models.SlugField(allow_unicode=True, blank=True, max_length=140, unique=True, verbose_name="Слаг")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("archived", models.BooleanField(default=False, verbose_name="В архиве")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлён")),
            ],
            options={
                "verbose_name": "производитель",
                "verbose_name_plural": "производители",
                "ordering": ("name",),
            },
        ),
        migrations.AddField(
            model_name="product",
            name="short_description",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Краткое описание"),
        ),
        migrations.AddField(
            model_name="product",
            name="sort_index",
            field=models.PositiveIntegerField(default=100, verbose_name="Индекс сортировки"),
        ),
        migrations.AddField(
            model_name="product",
            name="is_featured",
            field=models.BooleanField(default=False, verbose_name="Топ-товар"),
        ),
        migrations.AddField(
            model_name="product",
            name="is_limited_edition",
            field=models.BooleanField(default=False, verbose_name="Ограниченный тираж"),
        ),
        migrations.AddField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to="shopapp.category",
                verbose_name="Категория",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="manufacturer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to="shopapp.manufacturer",
                verbose_name="Производитель",
            ),
        ),
        migrations.AlterModelOptions(
            name="product",
            options={"ordering": ("sort_index", "name"), "verbose_name": "товар", "verbose_name_plural": "товары"},
        ),
        migrations.AlterModelOptions(
            name="order",
            options={"ordering": ("-created_at",), "verbose_name": "заказ", "verbose_name_plural": "заказы"},
        ),
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(max_length=100, unique=True, verbose_name="Название"),
        ),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(verbose_name="Описание"),
        ),
        migrations.AlterField(
            model_name="product",
            name="image",
            field=models.ImageField(blank=True, upload_to=shopapp.models.product_image_upload_to, verbose_name="Изображение"),
        ),
        migrations.AlterField(
            model_name="product",
            name="price",
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Цена"),
        ),
        migrations.AlterField(
            model_name="product",
            name="discount",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="Скидка, %"),
        ),
        migrations.AlterField(
            model_name="product",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Создан"),
        ),
        migrations.AlterField(
            model_name="product",
            name="archived",
            field=models.BooleanField(default=False, verbose_name="В архиве"),
        ),
        migrations.AlterField(
            model_name="product",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to="auth.user",
                verbose_name="Автор",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="delivery_address",
            field=models.TextField(verbose_name="Адрес доставки"),
        ),
        migrations.AlterField(
            model_name="order",
            name="promo_code",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="Промокод"),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(default="new", max_length=32, verbose_name="Статус"),
        ),
        migrations.AlterField(
            model_name="order",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Создан"),
        ),
        migrations.AlterField(
            model_name="order",
            name="archived",
            field=models.BooleanField(default=False, verbose_name="В архиве"),
        ),
        migrations.AlterField(
            model_name="order",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="orders",
                to="auth.user",
                verbose_name="Пользователь",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="products",
            field=models.ManyToManyField(blank=True, related_name="orders", to="shopapp.product", verbose_name="Товары"),
        ),
    ]