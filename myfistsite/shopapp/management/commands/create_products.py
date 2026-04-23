from decimal import Decimal

from django.core.management.base import BaseCommand

from shopapp.models import Product


PRODUCTS = [
    {
        "name": "Ноутбук",
        "description": "Единственный товар, который совпал с картинкой, аллилуйя!",
        "price": Decimal("999999.99"),
        "discount": 10,
        "archived": False,
    },
    {
        "name": "Дрон 2",
        "description": "Когда первый кто то сломает (можно сразу оба заказывать).",
        "price": Decimal("2500.50"),
        "discount": 5,
        "archived": False,
    },
    {
        "name": "Видеокарта NAGIBATOR 3000",
        "description": "Покупаете и вы соответствуете названию видеокарты!",
        "price": Decimal("80000.00"),
        "discount": 10,
        "archived": False,
    },
    {
        "name": "Набор джентельмена",
        "description": "Планшет, голубая клава и палочка для ковыряния в ухе.",
        "price": Decimal("320.00"),
        "discount": 0,
        "archived": False,
    },
    {
        "name": "Ноутбук",
        "description": "С ним вы выглядите богаче, а еще можно подсвечивать тёмный переулок.",
        "price": Decimal("4005.90"),
        "discount": 0,
        "archived": False,
    },
    {
        "name": "Дрон",
        "description": "Пугать соседских кошек и алкоголиков.",
        "price": Decimal("1200.00"),
        "discount": 20,
        "archived": False,
    },
]


class Command(BaseCommand):
    help = "Создаёт демонстрационные товары через get_or_create"

    def handle(self, *args, **options):
        created_count = 0
        existed_count = 0

        for item in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "price": item["price"],
                    "discount": item["discount"],
                    "archived": item["archived"],
                },
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Создан товар: {product.name}"))
            else:
                existed_count += 1
                self.stdout.write(self.style.WARNING(f"Товар уже существует: {product.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Создано: {created_count}, уже существовало: {existed_count}."
            )
        )
