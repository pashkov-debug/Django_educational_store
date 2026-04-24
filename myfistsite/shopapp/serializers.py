from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from .models import Order, Product


class ProductSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    purchases_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "description",
            "image",
            "price",
            "discount",
            "final_price",
            "has_discount",
            "created_at",
            "created_by",
            "purchases_count",
        )
        read_only_fields = ("created_at", "created_by", "final_price", "has_discount", "purchases_count")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше нуля.")
        return value

    def validate_discount(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Скидка должна быть в диапазоне от 0 до 100.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        allow_null=True,
        required=False,
    )
    products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.none(), many=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "delivery_address",
            "promo_code",
            "status",
            "created_at",
            "user",
            "products",
            "total_price",
            "products_count",
        )
        read_only_fields = ("created_at", "total_price", "products_count")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        products_queryset = Product.objects.filter(archived=False)

        instance = getattr(self, "instance", None)
        if isinstance(instance, Order):
            current_product_ids = instance.products.values_list("pk", flat=True)
            products_queryset = Product.objects.filter(
                Q(archived=False) | Q(pk__in=current_product_ids)
            )

        self.fields["products"].queryset = products_queryset.order_by("name").distinct()

    def validate_delivery_address(self, value):
        delivery_address = value.strip()
        if len(delivery_address) < 10:
            raise serializers.ValidationError("Укажите более полный адрес доставки.")
        return delivery_address

    def validate_products(self, value):
        if not value:
            raise serializers.ValidationError("Выберите хотя бы один товар.")
        return value