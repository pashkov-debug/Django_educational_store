import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0014_checkout_order_items"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("account_number", models.CharField(max_length=8, verbose_name="Номер счёта или карты")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Сумма платежа")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Ожидает обработки"),
                            ("paid", "Оплачен"),
                            ("failed", "Ошибка оплаты"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=32,
                        verbose_name="Статус платежа",
                    ),
                ),
                ("error_message", models.TextField(blank=True, default="", verbose_name="Ошибка")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("processed_at", models.DateTimeField(blank=True, null=True, verbose_name="Обработан")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="shopapp.order",
                        verbose_name="Заказ",
                    ),
                ),
            ],
            options={
                "verbose_name": "платёж",
                "verbose_name_plural": "платежи",
                "ordering": ("-created_at",),
            },
        ),
    ]