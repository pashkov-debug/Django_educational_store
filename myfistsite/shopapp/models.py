
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def product_image_upload_to(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".jpg"
    return f"products/{uuid4().hex}{extension}"


class Category(models.Model):
    title = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="children",
        null=True,
        blank=True,
    )
    icon = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    sort_index = models.PositiveIntegerField(default=0)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ("sort_index", "title")
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or f"category-{self.pk or 'new'}"
            slug = base_slug
            suffix = 1
            while Category.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100, unique=True)
    short_description = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField()
    image = models.ImageField(
        _("Image"),
        upload_to=product_image_upload_to,
        blank=True,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.PositiveSmallIntegerField(default=0)
    manufacturer = models.CharField(max_length=120, blank=True, default="")
    sort_index = models.PositiveIntegerField(default=0)
    limited_edition = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Author"),
    )

    class Meta:
        ordering = ("sort_index", "name")
        verbose_name = _("product")
        verbose_name_plural = _("products")

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("shopapp:product_detail", kwargs={"pk": self.pk})

    @property
    def final_price(self) -> Decimal:
        price = self.price or Decimal("0")
        if not self.discount:
            return price
        return (price * (Decimal("100") - Decimal(str(self.discount))) / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def has_discount(self) -> bool:
        return self.discount > 0

    @property
    def orders_count(self) -> int:
        if hasattr(self, "order_lines_count"):
            return int(self.order_lines_count or 0)
        return self.orders.count()

    @property
    def images_count(self) -> int:
        return 1 if self.image else 0

    @property
    def reviews_count(self) -> int:
        if hasattr(self, "reviews_total"):
            return int(self.reviews_total or 0)
        return self.reviews.filter(is_active=True).count()


class Order(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_NEW = "new"
    STATUS_PAID = "paid"
    STATUS_PAYMENT_ERROR = "payment_error"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_NEW, "New"),
        (STATUS_PAID, "Paid"),
        (STATUS_PAYMENT_ERROR, "Payment error"),
    )

    DELIVERY_REGULAR = "delivery"
    DELIVERY_EXPRESS = "express"
    DELIVERY_CHOICES = (
        (DELIVERY_REGULAR, "Delivery"),
        (DELIVERY_EXPRESS, "Express delivery"),
    )

    PAYMENT_CARD = "card"
    PAYMENT_RANDOM = "random_account"
    PAYMENT_CHOICES = (
        (PAYMENT_CARD, "Online card"),
        (PAYMENT_RANDOM, "Online from random account"),
    )

    delivery_address = models.TextField(blank=True, default="")
    promo_code = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=32, default=STATUS_DRAFT, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
    )
    products = models.ManyToManyField(
        Product,
        related_name="orders",
        blank=True,
    )
    full_name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    city = models.CharField(max_length=120, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    delivery_type = models.CharField(max_length=32, blank=True, default=DELIVERY_REGULAR, choices=DELIVERY_CHOICES)
    payment_type = models.CharField(max_length=32, blank=True, default=PAYMENT_CARD, choices=PAYMENT_CHOICES)
    comment = models.TextField(blank=True, default="")
    payment_error = models.CharField(max_length=255, blank=True, default="")
    payment_number = models.CharField(max_length=8, blank=True, default="")
    payment_attempted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("order")
        verbose_name_plural = _("orders")

    def __str__(self) -> str:
        return f"Order {self.pk}"

    @property
    def total_price(self) -> Decimal:
        if self.items.exists():
            total = sum((item.total_price for item in self.items.all()), Decimal("0"))
        else:
            total = sum((product.final_price for product in self.products.all()), Decimal("0"))
        return total.quantize(Decimal("0.01")) if isinstance(total, Decimal) else Decimal(str(total)).quantize(Decimal("0.01"))

    @property
    def delivery_cost(self) -> Decimal:
        settings_obj = ShopSettings.get_solo()
        subtotal = self.items_subtotal
        if self.delivery_type == self.DELIVERY_EXPRESS:
            return settings_obj.express_delivery_cost
        if subtotal >= settings_obj.free_delivery_threshold:
            return Decimal("0.00")
        return settings_obj.delivery_cost

    @property
    def items_subtotal(self) -> Decimal:
        if self.items.exists():
            subtotal = sum((item.total_price for item in self.items.all()), Decimal("0"))
        else:
            subtotal = sum((product.final_price for product in self.products.all()), Decimal("0"))
        return subtotal.quantize(Decimal("0.01")) if isinstance(subtotal, Decimal) else Decimal(str(subtotal)).quantize(Decimal("0.01"))

    @property
    def grand_total(self) -> Decimal:
        return (self.items_subtotal + self.delivery_cost).quantize(Decimal("0.01"))

    @property
    def products_count(self) -> int:
        if self.items.exists():
            return int(sum(item.quantity for item in self.items.all()))
        return self.products.count()

    def sync_delivery_address(self):
        city = (self.city or "").strip()
        address = (self.address or "").strip()
        combined = ", ".join(part for part in [city, address] if part)
        self.delivery_address = combined

    def mark_payment_pending(self, number: str):
        self.payment_number = number
        self.payment_attempted_at = timezone.now()
        self.status = self.STATUS_NEW
        self.payment_error = ""


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ("pk",)
        unique_together = ("order", "product")
        verbose_name = _("order item")
        verbose_name_plural = _("order items")

    def __str__(self) -> str:
        return f"{self.order_id}: {self.product_id} x {self.quantity}"

    @property
    def total_price(self) -> Decimal:
        return (self.price_snapshot * self.quantity).quantize(Decimal("0.01"))


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviews",
        null=True,
        blank=True,
    )
    author = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    text = models.TextField()
    rate = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("review")
        verbose_name_plural = _("reviews")

    def __str__(self) -> str:
        return f"Review {self.pk} for {self.product_id}"


class ShopSettings(models.Model):
    singleton_key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=200)
    express_delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=500)

    class Meta:
        verbose_name = _("shop settings")
        verbose_name_plural = _("shop settings")

    def __str__(self) -> str:
        return "Store settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"singleton_key": 1})
        return obj
