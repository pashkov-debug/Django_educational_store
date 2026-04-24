from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def product_image_upload_to(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".jpg"
    return f"products/{uuid4().hex}{extension}"


def category_icon_upload_to(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".svg"
    return f"categories/{uuid4().hex}{extension}"


class Category(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    slug = models.SlugField("Слаг", max_length=140, unique=True, blank=True, allow_unicode=True)
    icon = models.ImageField("Иконка", upload_to=category_icon_upload_to, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        null=True,
        blank=True,
        verbose_name="Родительская категория",
    )
    is_active = models.BooleanField("Активна", default=True)
    is_featured = models.BooleanField("Избранная на главной", default=False)
    sort_index = models.PositiveIntegerField("Индекс сортировки", default=100)
    archived = models.BooleanField("В архиве", default=False)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ("sort_index", "name")
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self) -> str:
        if self.parent_id:
            return f"{self.parent.name} / {self.name}"
        return self.name

    def clean(self):
        if self.parent_id and self.parent.parent_id:
            raise ValidationError({"parent": "Максимальная вложенность категорий — 2 уровня."})
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "Категория не может быть родителем самой себя."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)[:120]
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return f"{reverse('shopapp:products_list')}?category={self.slug}"


class Manufacturer(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    slug = models.SlugField("Слаг", max_length=140, unique=True, blank=True, allow_unicode=True)
    description = models.TextField("Описание", blank=True)
    archived = models.BooleanField("В архиве", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "производитель"
        verbose_name_plural = "производители"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)[:120]
        self.full_clean()
        return super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    short_description = models.CharField("Краткое описание", max_length=255, blank=True, default="")
    description = models.TextField("Описание")
    image = models.ImageField("Изображение", upload_to=product_image_upload_to, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
        blank=True,
        verbose_name="Категория",
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
        blank=True,
        verbose_name="Производитель",
    )
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    discount = models.PositiveSmallIntegerField("Скидка, %", default=0)
    sort_index = models.PositiveIntegerField("Индекс сортировки", default=100)
    is_featured = models.BooleanField("Топ-товар", default=False)
    is_limited_edition = models.BooleanField("Ограниченный тираж", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    archived = models.BooleanField("В архиве", default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
        blank=True,
        verbose_name="Автор",
    )

    class Meta:
        ordering = ("sort_index", "name")
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("shopapp:product_detail", kwargs={"pk": self.pk})

    @property
    def display_description(self) -> str:
        return self.short_description or self.description

    @property
    def final_price(self) -> Decimal:
        price = self.price or Decimal("0.00")
        if not self.discount:
            return price
        return price * (Decimal("100") - Decimal(str(self.discount))) / Decimal("100")

    @property
    def has_discount(self) -> bool:
        return self.discount > 0

    @property
    def orders_count(self) -> int:
        annotated_value = getattr(self, "orders_count_value", None)
        if annotated_value is not None:
            return annotated_value
        return self.orders.count()

    @property
    def purchases_count(self) -> int:
        annotated_value = getattr(self, "_purchases_count", None)
        if annotated_value is not None:
            return annotated_value
        return self.orders_count

    @purchases_count.setter
    def purchases_count(self, value: int) -> None:
        self._purchases_count = value

    @property
    def reviews_count(self) -> int:
        annotated_value = getattr(self, "reviews_count_value", None)
        if annotated_value is not None:
            return annotated_value
        if hasattr(self, "reviews"):
            return self.reviews.count()
        return 0

    @property
    def images_count(self) -> int:
        return 1 if self.image else 0


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )
    session_key = models.CharField("Ключ сессии", max_length=64, blank=True, db_index=True)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "корзина"
        verbose_name_plural = "корзины"
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=models.Q(is_active=True, user__isnull=False),
                name="uniq_active_cart_for_user",
            ),
            models.UniqueConstraint(
                fields=("session_key",),
                condition=models.Q(is_active=True, user__isnull=True),
                name="uniq_active_cart_for_session",
            ),
        ]

    def __str__(self) -> str:
        if self.user_id:
            return f"Корзина пользователя {self.user}"
        return f"Гостевая корзина {self.session_key or self.pk}"

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.total_price
        return total

    @property
    def is_empty(self) -> bool:
        return self.items.count() == 0


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="Корзина")
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="cart_items",
        verbose_name="Товар",
    )
    quantity = models.PositiveIntegerField("Количество", default=1)
    price_snapshot = models.DecimalField("Цена на момент добавления", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ("created_at", "pk")
        verbose_name = "позиция корзины"
        verbose_name_plural = "позиции корзины"
        constraints = [
            models.UniqueConstraint(fields=("cart", "product"), name="uniq_cart_product_item"),
        ]

    def __str__(self) -> str:
        return f"{self.product} × {self.quantity}"

    @property
    def total_price(self) -> Decimal:
        return self.price_snapshot * self.quantity

    def clean(self):
        if self.quantity < 1:
            raise ValidationError({"quantity": "Количество должно быть больше нуля."})

    def save(self, *args, **kwargs):
        if self.price_snapshot is None:
            self.price_snapshot = self.product.final_price
        self.full_clean()
        return super().save(*args, **kwargs)


class ShopSettings(models.Model):
    regular_delivery_price = models.DecimalField(
        "Стоимость обычной доставки",
        max_digits=10,
        decimal_places=2,
        default=Decimal("200.00"),
    )
    free_delivery_threshold = models.DecimalField(
        "Бесплатная доставка от",
        max_digits=10,
        decimal_places=2,
        default=Decimal("2000.00"),
    )
    express_delivery_price = models.DecimalField(
        "Стоимость экспресс-доставки",
        max_digits=10,
        decimal_places=2,
        default=Decimal("500.00"),
    )
    updated_at = models.DateTimeField("Обновлены", auto_now=True)

    class Meta:
        verbose_name = "настройки магазина"
        verbose_name_plural = "настройки магазина"

    def __str__(self) -> str:
        return "Настройки магазина"

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        settings_object, _ = cls.objects.get_or_create(pk=1)
        return settings_object

    def calculate_delivery_price(self, *, cart_total: Decimal, delivery_type: str) -> Decimal:
        if delivery_type == Order.DeliveryType.EXPRESS:
            return self.express_delivery_price

        if cart_total >= self.free_delivery_threshold:
            return Decimal("0.00")

        return self.regular_delivery_price


class Order(models.Model):
    class DeliveryType(models.TextChoices):
        REGULAR = "regular", "Доставка"
        EXPRESS = "express", "Экспресс-доставка"

    class PaymentType(models.TextChoices):
        CARD = "card", "Онлайн картой"
        RANDOM_ACCOUNT = "random_account", "Онлайн со случайного чужого счёта"

    class PaymentStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Не начата"
        PENDING = "pending", "Ожидает оплаты"
        PAID = "paid", "Оплачен"
        FAILED = "failed", "Ошибка оплаты"

    delivery_address = models.TextField("Адрес доставки")
    promo_code = models.CharField("Промокод", max_length=64, blank=True, default="")
    status = models.CharField("Статус", max_length=32, default="new")
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    archived = models.BooleanField("В архиве", default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )
    products = models.ManyToManyField(Product, related_name="orders", blank=True, verbose_name="Товары")

    full_name = models.CharField("Ф. И. О.", max_length=255, blank=True, default="")
    email = models.EmailField("Email", blank=True, default="")
    phone = models.CharField("Телефон", max_length=32, blank=True, default="")
    city = models.CharField("Город", max_length=120, blank=True, default="")
    address = models.CharField("Адрес", max_length=255, blank=True, default="")
    delivery_type = models.CharField(
        "Способ доставки",
        max_length=32,
        choices=DeliveryType.choices,
        default=DeliveryType.REGULAR,
    )
    delivery_price = models.DecimalField("Стоимость доставки", max_digits=10, decimal_places=2, default=Decimal("0.00"))
    payment_type = models.CharField(
        "Способ оплаты",
        max_length=32,
        choices=PaymentType.choices,
        default=PaymentType.CARD,
    )
    payment_status = models.CharField(
        "Статус оплаты",
        max_length=32,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_STARTED,
    )
    payment_error = models.TextField("Ошибка оплаты", blank=True, default="")
    comment = models.TextField("Комментарий к заказу", blank=True, default="")
    total_price_snapshot = models.DecimalField(
        "Итоговая сумма заказа",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "заказ"
        verbose_name_plural = "заказы"

    def __str__(self) -> str:
        return f"Заказ {self.pk}"

    @property
    def items_price(self) -> Decimal:
        if self.items.exists():
            total = Decimal("0.00")
            for item in self.items.all():
                total += item.total_price
            return total

        total = Decimal("0.00")
        for product in self.products.all():
            total += product.final_price
        return total

    @property
    def total_price(self) -> Decimal:
        if self.total_price_snapshot:
            return self.total_price_snapshot
        return self.items_price + self.delivery_price

    @property
    def products_count(self) -> int:
        if self.items.exists():
            return sum(item.quantity for item in self.items.all())
        return self.products.count()

    @property
    def delivery_type_label(self) -> str:
        return self.DeliveryType(self.delivery_type).label

    @property
    def payment_type_label(self) -> str:
        return self.PaymentType(self.payment_type).label

    @property
    def payment_status_label(self) -> str:
        return self.PaymentStatus(self.payment_status).label


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Товар",
    )
    product_name_snapshot = models.CharField("Название товара на момент заказа", max_length=255)
    quantity = models.PositiveIntegerField("Количество", default=1)
    unit_price = models.DecimalField("Цена за единицу", max_digits=10, decimal_places=2)
    total_price = models.DecimalField("Сумма позиции", max_digits=10, decimal_places=2)

    class Meta:
        ordering = ("pk",)
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"

    def __str__(self) -> str:
        return f"{self.product_name_snapshot} × {self.quantity}"

    def save(self, *args, **kwargs):
        self.product_name_snapshot = self.product_name_snapshot or self.product.name
        self.total_price = self.unit_price * self.quantity
        self.full_clean()
        return super().save(*args, **kwargs)


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает обработки"
        PAID = "paid", "Оплачен"
        FAILED = "failed", "Ошибка оплаты"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Заказ",
    )
    account_number = models.CharField("Номер счёта или карты", max_length=8)
    amount = models.DecimalField("Сумма платежа", max_digits=10, decimal_places=2)
    status = models.CharField(
        "Статус платежа",
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    error_message = models.TextField("Ошибка", blank=True, default="")
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    processed_at = models.DateTimeField("Обработан", null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "платёж"
        verbose_name_plural = "платежи"

    def __str__(self) -> str:
        return f"Платёж #{self.pk} по заказу #{self.order_id}"

    @property
    def status_label(self) -> str:
        return self.Status(self.status).label