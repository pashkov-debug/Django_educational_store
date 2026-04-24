from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from shopapp.models import Category, Manufacturer, Order, Product


class Command(BaseCommand):
    help = "Заполняет сайт демонстрационными данными для локальной проверки storefront."

    ADMIN_USERNAME = "admin_demo"
    ADMIN_PASSWORD = "admin123456"
    BUYER_PASSWORD = "123456"

    CATEGORY_DATA = [
        {
            "name": "Электроника",
            "slug": "electronics",
            "is_featured": True,
            "sort_index": 1,
            "children": [
                {"name": "Смартфоны", "slug": "smartphones", "sort_index": 1},
                {"name": "Ноутбуки", "slug": "laptops", "sort_index": 2},
            ],
        },
        {
            "name": "Бытовая техника",
            "slug": "home-appliances",
            "is_featured": True,
            "sort_index": 2,
            "children": [
                {"name": "Холодильники", "slug": "refrigerators", "sort_index": 1},
                {"name": "Стиральные машины", "slug": "washing-machines", "sort_index": 2},
            ],
        },
        {
            "name": "Дом и дача",
            "slug": "home-and-garden",
            "is_featured": True,
            "sort_index": 3,
            "children": [
                {"name": "Инструменты", "slug": "tools", "sort_index": 1},
                {"name": "Освещение", "slug": "lighting", "sort_index": 2},
            ],
        },
    ]

    MANUFACTURER_DATA = [
        {
            "name": "SkillPhone",
            "slug": "skillphone",
            "description": "Производитель смартфонов и аксессуаров.",
        },
        {
            "name": "DjangoBook",
            "slug": "djangobook",
            "description": "Производитель ноутбуков для работы и учёбы.",
        },
        {
            "name": "CleanHome",
            "slug": "cleanhome",
            "description": "Бренд бытовой техники.",
        },
        {
            "name": "GardenPro",
            "slug": "gardenpro",
            "description": "Товары для дома, ремонта и дачи.",
        },
    ]

    PRODUCT_DATA = [
        {
            "name": "Смартфон SkillPhone X",
            "slug_category": "smartphones",
            "slug_manufacturer": "skillphone",
            "price": "49990.00",
            "discount": 10,
            "sort_index": 1,
            "is_featured": True,
            "is_limited_edition": True,
        },
        {
            "name": "Смартфон SkillPhone Lite",
            "slug_category": "smartphones",
            "slug_manufacturer": "skillphone",
            "price": "19990.00",
            "discount": 0,
            "sort_index": 2,
            "is_featured": True,
            "is_limited_edition": False,
        },
        {
            "name": "Ноутбук DjangoBook Pro 14",
            "slug_category": "laptops",
            "slug_manufacturer": "djangobook",
            "price": "89990.00",
            "discount": 5,
            "sort_index": 3,
            "is_featured": True,
            "is_limited_edition": True,
        },
        {
            "name": "Ноутбук DjangoBook Air 13",
            "slug_category": "laptops",
            "slug_manufacturer": "djangobook",
            "price": "69990.00",
            "discount": 0,
            "sort_index": 4,
            "is_featured": True,
            "is_limited_edition": False,
        },
        {
            "name": "Холодильник CleanHome Frost",
            "slug_category": "refrigerators",
            "slug_manufacturer": "cleanhome",
            "price": "54990.00",
            "discount": 7,
            "sort_index": 5,
            "is_featured": False,
            "is_limited_edition": True,
        },
        {
            "name": "Стиральная машина CleanHome Wash",
            "slug_category": "washing-machines",
            "slug_manufacturer": "cleanhome",
            "price": "37990.00",
            "discount": 0,
            "sort_index": 6,
            "is_featured": False,
            "is_limited_edition": False,
        },
        {
            "name": "Набор инструментов GardenPro Master",
            "slug_category": "tools",
            "slug_manufacturer": "gardenpro",
            "price": "7990.00",
            "discount": 15,
            "sort_index": 7,
            "is_featured": False,
            "is_limited_edition": True,
        },
        {
            "name": "Светильник GardenPro Light",
            "slug_category": "lighting",
            "slug_manufacturer": "gardenpro",
            "price": "2990.00",
            "discount": 0,
            "sort_index": 8,
            "is_featured": False,
            "is_limited_edition": False,
        },
        {
            "name": "Умная лампа GardenPro Smart",
            "slug_category": "lighting",
            "slug_manufacturer": "gardenpro",
            "price": "1490.00",
            "discount": 0,
            "sort_index": 9,
            "is_featured": False,
            "is_limited_edition": False,
        },
        {
            "name": "Портативная колонка SkillPhone Sound",
            "slug_category": "electronics",
            "slug_manufacturer": "skillphone",
            "price": "5990.00",
            "discount": 12,
            "sort_index": 10,
            "is_featured": False,
            "is_limited_edition": True,
        },
    ]

    BUYER_DATA = [
        {
            "username": "buyer_demo_1",
            "email": "buyer1@example.com",
            "first_name": "Иван",
            "last_name": "Покупатель",
        },
        {
            "username": "buyer_demo_2",
            "email": "buyer2@example.com",
            "first_name": "Мария",
            "last_name": "Клиентова",
        },
        {
            "username": "buyer_demo_3",
            "email": "buyer3@example.com",
            "first_name": "Пётр",
            "last_name": "Заказов",
        },
    ]

    ORDER_DATA = [
        {
            "promo_code": "DEMO-ORDER-001",
            "buyer_username": "buyer_demo_1",
            "delivery_address": "Москва, ул. Примерная, дом 1",
            "product_names": ["Смартфон SkillPhone X", "Светильник GardenPro Light"],
            "status": "paid",
        },
        {
            "promo_code": "DEMO-ORDER-002",
            "buyer_username": "buyer_demo_2",
            "delivery_address": "Санкт-Петербург, Невский проспект, дом 10",
            "product_names": ["Ноутбук DjangoBook Pro 14"],
            "status": "new",
        },
        {
            "promo_code": "DEMO-ORDER-003",
            "buyer_username": "buyer_demo_3",
            "delivery_address": "Казань, ул. Кремлёвская, дом 5",
            "product_names": [
                "Холодильник CleanHome Frost",
                "Стиральная машина CleanHome Wash",
                "Набор инструментов GardenPro Master",
            ],
            "status": "processing",
        },
        {
            "promo_code": "DEMO-ORDER-004",
            "buyer_username": "buyer_demo_1",
            "delivery_address": "Москва, ул. Примерная, дом 1",
            "product_names": ["Смартфон SkillPhone X", "Ноутбук DjangoBook Air 13"],
            "status": "paid",
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить демо-данные перед повторным заполнением.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.reset_demo_data()

        groups = self.create_groups()
        users = self.create_users(groups=groups)
        categories = self.create_categories()
        manufacturers = self.create_manufacturers()
        products = self.create_products(categories=categories, manufacturers=manufacturers)
        orders = self.create_orders(users=users, products=products)

        self.stdout.write(self.style.SUCCESS("Демо-данные успешно созданы."))
        self.stdout.write("")
        self.stdout.write("Доступы:")
        self.stdout.write(f"  Админ: {self.ADMIN_USERNAME} / {self.ADMIN_PASSWORD}")
        self.stdout.write(f"  Покупатели: buyer_demo_1..3 / {self.BUYER_PASSWORD}")
        self.stdout.write("")
        self.stdout.write("Проверить:")
        self.stdout.write("  /")
        self.stdout.write("  /catalog/")
        self.stdout.write("  /cart/")
        self.stdout.write("")
        self.stdout.write(
            f"Создано/обновлено: категории={len(categories)}, производители={len(manufacturers)}, "
            f"товары={len(products)}, заказы={len(orders)}."
        )

    def reset_demo_data(self):
        Product.objects.filter(name__in=[item["name"] for item in self.PRODUCT_DATA]).delete()
        Order.objects.filter(promo_code__startswith="DEMO-ORDER-").delete()

        for category_slug in self.get_child_category_slugs():
            Category.objects.filter(slug=category_slug).delete()

        for category_slug in self.get_parent_category_slugs():
            Category.objects.filter(slug=category_slug).delete()

        Manufacturer.objects.filter(slug__in=[item["slug"] for item in self.MANUFACTURER_DATA]).delete()

        user_model = get_user_model()
        demo_usernames = [self.ADMIN_USERNAME, *[item["username"] for item in self.BUYER_DATA]]
        user_model.objects.filter(username__in=demo_usernames).delete()

    def create_groups(self) -> dict[str, Group]:
        buyer_group, _ = Group.objects.get_or_create(name="Покупатель")
        admin_group, _ = Group.objects.get_or_create(name="Администратор")

        return {
            "buyer": buyer_group,
            "admin": admin_group,
        }

    def create_users(self, *, groups: dict[str, Group]):
        user_model = get_user_model()

        admin, created = user_model.objects.get_or_create(
            username=self.ADMIN_USERNAME,
            defaults={
                "email": "admin@example.com",
                "first_name": "Админ",
                "last_name": "Демо",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.email = "admin@example.com"
        admin.first_name = "Админ"
        admin.last_name = "Демо"
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(self.ADMIN_PASSWORD)
        admin.save()
        admin.groups.add(groups["admin"])

        users = {
            self.ADMIN_USERNAME: admin,
        }

        for buyer_data in self.BUYER_DATA:
            buyer, _ = user_model.objects.get_or_create(
                username=buyer_data["username"],
                defaults={
                    "email": buyer_data["email"],
                    "first_name": buyer_data["first_name"],
                    "last_name": buyer_data["last_name"],
                },
            )
            buyer.email = buyer_data["email"]
            buyer.first_name = buyer_data["first_name"]
            buyer.last_name = buyer_data["last_name"]
            buyer.is_staff = False
            buyer.is_superuser = False
            buyer.set_password(self.BUYER_PASSWORD)
            buyer.save()
            buyer.groups.add(groups["buyer"])
            users[buyer.username] = buyer

        return users

    def create_categories(self) -> dict[str, Category]:
        categories = {}

        for category_data in self.CATEGORY_DATA:
            parent, _ = Category.objects.update_or_create(
                slug=category_data["slug"],
                defaults={
                    "name": category_data["name"],
                    "parent": None,
                    "is_active": True,
                    "is_featured": category_data["is_featured"],
                    "sort_index": category_data["sort_index"],
                    "archived": False,
                },
            )
            categories[parent.slug] = parent

            for child_data in category_data["children"]:
                child, _ = Category.objects.update_or_create(
                    slug=child_data["slug"],
                    defaults={
                        "name": child_data["name"],
                        "parent": parent,
                        "is_active": True,
                        "is_featured": False,
                        "sort_index": child_data["sort_index"],
                        "archived": False,
                    },
                )
                categories[child.slug] = child

        return categories

    def create_manufacturers(self) -> dict[str, Manufacturer]:
        manufacturers = {}

        for manufacturer_data in self.MANUFACTURER_DATA:
            manufacturer, _ = Manufacturer.objects.update_or_create(
                slug=manufacturer_data["slug"],
                defaults={
                    "name": manufacturer_data["name"],
                    "description": manufacturer_data["description"],
                    "archived": False,
                },
            )
            manufacturers[manufacturer.slug] = manufacturer

        return manufacturers

    def create_products(
        self,
        *,
        categories: dict[str, Category],
        manufacturers: dict[str, Manufacturer],
    ) -> dict[str, Product]:
        products = {}

        for product_data in self.PRODUCT_DATA:
            product, _ = Product.objects.update_or_create(
                name=product_data["name"],
                defaults={
                    "short_description": f"Краткое описание товара «{product_data['name']}».",
                    "description": (
                        f"Подробное описание товара «{product_data['name']}». "
                        "Демо-товар используется для проверки каталога, фильтров, сортировки и корзины."
                    ),
                    "category": categories[product_data["slug_category"]],
                    "manufacturer": manufacturers[product_data["slug_manufacturer"]],
                    "price": Decimal(product_data["price"]),
                    "discount": product_data["discount"],
                    "sort_index": product_data["sort_index"],
                    "is_featured": product_data["is_featured"],
                    "is_limited_edition": product_data["is_limited_edition"],
                    "archived": False,
                },
            )
            products[product.name] = product

        return products

    def create_orders(self, *, users: dict, products: dict[str, Product]) -> list[Order]:
        orders = []

        for order_data in self.ORDER_DATA:
            order = Order.objects.filter(promo_code=order_data["promo_code"]).first()

            if order is None:
                order = Order.objects.create(
                    promo_code=order_data["promo_code"],
                    delivery_address=order_data["delivery_address"],
                    status=order_data["status"],
                    user=users[order_data["buyer_username"]],
                )
            else:
                order.delivery_address = order_data["delivery_address"]
                order.status = order_data["status"]
                order.user = users[order_data["buyer_username"]]
                order.archived = False
                order.save()

            order.products.set([products[name] for name in order_data["product_names"]])
            orders.append(order)

        return orders

    def get_parent_category_slugs(self) -> list[str]:
        return [category["slug"] for category in self.CATEGORY_DATA]

    def get_child_category_slugs(self) -> list[str]:
        return [
            child["slug"]
            for category in self.CATEGORY_DATA
            for child in category["children"]
        ]