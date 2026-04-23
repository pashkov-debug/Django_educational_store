
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = "frontend/index.html"


class CatalogPageView(TemplateView):
    template_name = "frontend/catalog.html"


class ProductPageView(TemplateView):
    template_name = "frontend/product.html"


class CartPageView(TemplateView):
    template_name = "frontend/cart.html"


class CheckoutPageView(TemplateView):
    template_name = "frontend/order.html"


class PaymentPageView(TemplateView):
    template_name = "frontend/payment.html"


class PaymentSomeonePageView(TemplateView):
    template_name = "frontend/paymentsomeone.html"


class SalePageView(TemplateView):
    template_name = "frontend/sale.html"


class AboutPageView(TemplateView):
    template_name = "frontend/about.html"


class SignInPageView(TemplateView):
    template_name = "frontend/signIn.html"


class SignUpPageView(TemplateView):
    template_name = "frontend/signUp.html"


class AccountPageView(LoginRequiredMixin, TemplateView):
    template_name = "frontend/account.html"


class ProfilePageView(LoginRequiredMixin, TemplateView):
    template_name = "frontend/profile.html"


class OrderHistoryPageView(LoginRequiredMixin, TemplateView):
    template_name = "frontend/historyorder.html"


class OrderDetailPageView(LoginRequiredMixin, TemplateView):
    template_name = "frontend/oneorder.html"
