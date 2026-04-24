from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Order


class UserOrderHistoryView(LoginRequiredMixin, ListView):
    template_name = "shopapp/storefront/order_history.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return (
            Order.objects.filter(
                user=self.request.user,
                archived=False,
            )
            .prefetch_related(
                "items",
                "items__product",
                "products",
                "payments",
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "История заказов"
        return context