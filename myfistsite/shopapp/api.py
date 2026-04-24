from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Order, Product
from .serializers import OrderSerializer, ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "description")
    ordering_fields = ("name", "price", "created_at", "purchases_count")
    ordering = ("name",)

    def get_queryset(self):
        return (
            Product.objects.filter(archived=False)
            .select_related("created_by")
            .annotate(
                purchases_count=Count(
                    "orders",
                    filter=Q(orders__archived=False),
                    distinct=True,
                )
            )
            .order_by(*self.ordering)
        )

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)

    def perform_destroy(self, instance):
        if not instance.archived:
            instance.archived = True
            instance.save(update_fields=["archived"])


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = {
        "status": ("exact",),
        "user": ("exact",),
        "promo_code": ("exact", "icontains"),
    }
    ordering_fields = ("id", "status", "created_at")
    ordering = ("-created_at",)

    def get_queryset(self):
        return (
            Order.objects.filter(archived=False)
            .select_related("user")
            .prefetch_related("products")
            .order_by(*self.ordering)
        )

    def perform_destroy(self, instance):
        if not instance.archived:
            instance.archived = True
            instance.save(update_fields=["archived"])
