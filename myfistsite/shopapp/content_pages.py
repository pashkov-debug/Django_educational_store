from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, RedirectView, TemplateView

from .models import Product


class AboutPageView(TemplateView):
    template_name = "shopapp/storefront/about.html"


class SalePageView(ListView):
    template_name = "shopapp/storefront/sale.html"
    context_object_name = "sale_products"
    paginate_by = 9

    def get_queryset(self):
        return (
            Product.objects.filter(
                archived=False,
                discount__gt=0,
            )
            .select_related("category", "manufacturer")
            .order_by("-discount", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Скидки"
        return context


class LegacyAccountRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False
    pattern_name = "accounts:account"


class LegacyProfileRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False
    pattern_name = "accounts:profile"


class LegacyProfileAvatarRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False
    pattern_name = "accounts:about_me"