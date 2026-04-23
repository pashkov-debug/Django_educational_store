from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from shopapp.models import Order, Product


class Command(BaseCommand):
    help = "Создаёт демонстрационные заказы и связывает их с существующими товарами, адаптировано под картинки и чувство юмора"

    def handle(self, *args, **options):
        user_model = get_user_model()
        user = user_model.objects.filter(is_superuser=True).first() or user_model.objects.first()

        if user is None:
            raise CommandError("Сначала создайте пользователя через python manage.py createsuperuser")

        products = {product.name: product for product in Product.objects.all()}
        if not products:
            raise CommandError("Сначала создайте товары через python manage.py create_products")

        orders_data = [
            {
                "delivery_address": "Москва, ул. Зачёт, д. 1",
                "status": "new",
                "product_names": ["Набор джентельмена", "Видеокарта NAGIBATOR 3000", "Дрон 2"],
            },
            {
                "delivery_address": "Санкт-Петербург, Солевой пр., д. 10",
                "status": "paid",
                "product_names": ["Набор джентельмена", "Смартфон"],
            },
            {
                "delivery_address": "Казань, ул. Примите Пожалуйста, д. 15",
                "status": "processing",
                "product_names": ["Дрон", "Дрон 2"],
            },
        ]

        created_count = 0
        existed_count = 0

        for item in orders_data:
            order, created = Order.objects.get_or_create(
                user=user,
                delivery_address=item["delivery_address"],
                defaults={"status": item["status"]},
            )

            selected_products = [products[name] for name in item["product_names"] if name in products]
            order.products.set(selected_products)

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Создан заказ #{order.pk}"))
            else:
                existed_count += 1
                self.stdout.write(self.style.WARNING(f"Заказ уже существует #{order.pk}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Создано заказов: {created_count}, уже существовало: {existed_count}."
            )
        )
