from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView

from .models import Order


class OrderDetailView(DetailView):
    template_name = "shopapp/storefront/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return (
            Order.objects.filter(archived=False)
            .select_related("user")
            .prefetch_related(
                "products",
                "items",
                "items__product",
            )
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.can_view_order(self.object):
            raise PermissionDenied("У вас нет доступа к этому заказу.")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object
        return super().get_object(queryset)

    def can_view_order(self, order: Order) -> bool:
        user = self.request.user

        if user.is_authenticated:
            if user.is_superuser or user.is_staff:
                return True

            if user.has_perm("shopapp.view_order"):
                return True

            if order.user_id == user.id:
                return True

        session_order_ids = {
            self.request.session.get("payment_order_id"),
            self.request.session.get("last_paid_order_id"),
        }

        return order.pk in session_order_ids

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        order_items = list(order.items.select_related("product").all())

        context.update(
            {
                "order_items": order_items,
                "products": list(order.products.all()),
                "products_count": order.products_count,
                "total_price": order.total_price,
            }
        )
        return context