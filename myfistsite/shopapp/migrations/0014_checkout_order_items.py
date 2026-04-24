from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0013_cart"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShopSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("regular_delivery_price", models.DecimalField(decimal_places=2, default=Decimal("200.00"), max_digits=10, verbose_name="Стоимость обычной доставки")),
                ("free_delivery_threshold", models.DecimalField(decimal_places=2, default=Decimal("2000.00"), max_digits=10, verbose_name="Бесплатная доставка от")),
                ("express_delivery_price", models.DecimalField(decimal_places=2, default=Decimal("500.00"), max_digits=10, verbose_name="Стоимость экспресс-доставки")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлены")),
            ],
            options={
                "verbose_name": "настройки магазина",
                "verbose_name_plural": "настройки магазина",
            },
        ),
        migrations.AddField(
            model_name="order",
            name="full_name",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Ф. И. О."),
        ),
        migrations.AddField(
            model_name="order",
            name="email",
            field=models.EmailField(blank=True, default="", max_length=254, verbose_name="Email"),
        ),
        migrations.AddField(
            model_name="order",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=32, verbose_name="Телефон"),
        ),
        migrations.AddField(
            model_name="order",
            name="city",
            field=models.CharField(blank=True, default="", max_length=120, verbose_name="Город"),
        ),
        migrations.AddField(
            model_name="order",
            name="address",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Адрес"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_type",
            field=models.CharField(choices=[("regular", "Доставка"), ("express", "Экспресс-доставка")], default="regular", max_length=32, verbose_name="Способ доставки"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, verbose_name="Стоимость доставки"),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_type",
            field=models.CharField(choices=[("card", "Онлайн картой"), ("random_account", "Онлайн со случайного чужого счёта")], default="card", max_length=32, verbose_name="Способ оплаты"),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_status",
            field=models.CharField(choices=[("not_started", "Не начата"), ("pending", "Ожидает оплаты"), ("paid", "Оплачен"), ("failed", "Ошибка оплаты")], default="not_started", max_length=32, verbose_name="Статус оплаты"),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_error",
            field=models.TextField(blank=True, default="", verbose_name="Ошибка оплаты"),
        ),
        migrations.AddField(
            model_name="order",
            name="comment",
            field=models.TextField(blank=True, default="", verbose_name="Комментарий к заказу"),
        ),
        migrations.AddField(
            model_name="order",
            name="total_price_snapshot",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, verbose_name="Итоговая сумма заказа"),
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name_snapshot", models.CharField(max_length=255, verbose_name="Название товара на момент заказа")),
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="Количество")),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Цена за единицу")),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Сумма позиции")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="shopapp.order", verbose_name="Заказ")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="shopapp.product", verbose_name="Товар")),
            ],
            options={
                "verbose_name": "позиция заказа",
                "verbose_name_plural": "позиции заказа",
                "ordering": ("pk",),
            },
        ),
    ]