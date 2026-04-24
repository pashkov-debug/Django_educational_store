from django import template
from django.db.models import Prefetch

from shopapp.cart import CartService
from shopapp.models import Category

register = template.Library()


@register.simple_tag
def active_categories():
    return (
        Category.objects.filter(archived=False, is_active=True, parent__isnull=True)
        .prefetch_related(
            Prefetch(
                "children",
                queryset=Category.objects.filter(archived=False, is_active=True).order_by("sort_index", "name"),
                to_attr="active_menu_children",
            )
        )
        .order_by("sort_index", "name")
    )


@register.simple_tag(takes_context=True)
def cart_summary(context):
    request = context.get("request")

    if request is None:
        return {
            "total_quantity": 0,
            "total_price": 0,
        }

    service = CartService(request)

    return {
        "total_quantity": service.get_total_quantity(),
        "total_price": service.get_total_price(),
    }