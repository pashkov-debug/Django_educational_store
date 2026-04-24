from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.views import View
from django.views.generic import FormView

from .cart import CartService
from .forms import (
    CheckoutConfirmForm,
    CheckoutCustomerForm,
    CheckoutDeliveryForm,
    CheckoutPaymentForm,
)
from .models import Cart, Order, OrderItem, ShopSettings

CHECKOUT_SESSION_KEY = "checkout"


class CheckoutSession:
    def __init__(self, request):
        self.request = request

    def get_state(self) -> dict:
        return self.request.session.get(CHECKOUT_SESSION_KEY, {})

    def update_step(self, step: str, data: dict) -> None:
        state = self.get_state()
        state[step] = data
        self.request.session[CHECKOUT_SESSION_KEY] = state
        self.request.session.modified = True

    def get_step(self, step: str) -> dict:
        return self.get_state().get(step, {})

    def clear(self) -> None:
        self.request.session.pop(CHECKOUT_SESSION_KEY, None)
        self.request.session.modified = True


class CheckoutCartMixin:
    def get_cart(self) -> Cart:
        cart = CartService(self.request).get_cart(create=False)

        if cart is None or cart.is_empty:
            messages.error(self.request, "Корзина пуста. Добавьте товары перед оформлением заказа.")
            raise PermissionDenied("Корзина пуста.")

        return cart

    def dispatch(self, request, *args, **kwargs):
        try:
            self.cart = self.get_cart()
        except PermissionDenied:
            return redirect("shopapp:layout_cart")

        self.checkout_session = CheckoutSession(request)
        return super().dispatch(request, *args, **kwargs)

    def get_cart_context(self) -> dict:
        return {
            "cart": self.cart,
            "cart_items": self.cart.items.select_related("product").all(),
            "cart_total_quantity": self.cart.total_quantity,
            "cart_items_price": self.cart.total_price,
        }


class CheckoutCustomerView(CheckoutCartMixin, FormView):
    template_name = "shopapp/storefront/checkout_customer.html"
    form_class = CheckoutCustomerForm

    def get_initial(self):
        initial = self.checkout_session.get_step("customer").copy()

        if self.request.user.is_authenticated:
            profile = getattr(self.request.user, "profile", None)

            if profile:
                initial.setdefault("full_name", profile.full_name)
                initial.setdefault("phone", profile.phone)

            full_name = " ".join(
                part for part in [self.request.user.first_name, self.request.user.last_name] if part
            ).strip()
            initial.setdefault("full_name", full_name or self.request.user.username)
            initial.setdefault("email", self.request.user.email)

        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, "Проверьте Ф. И. О., email и телефон.")
        return super().form_invalid(form)

    def form_valid(self, form):
        customer_data = form.cleaned_data.copy()
        password = customer_data.pop("password", "")
        customer_data.pop("password_confirm", "")

        if not self.request.user.is_authenticated and password:
            user = self.create_user_from_checkout(customer_data, password)
            login(self.request, user)

        self.checkout_session.update_step("customer", customer_data)
        return redirect("shopapp:checkout_delivery")

    def create_user_from_checkout(self, customer_data: dict, password: str):
        user_model = get_user_model()
        email = customer_data["email"]
        username_base = email.split("@")[0] or "buyer"
        username = username_base
        index = 1

        while user_model.objects.filter(username=username).exists():
            index += 1
            username = f"{username_base}_{index}"

        full_name_parts = customer_data["full_name"].split(maxsplit=1)
        first_name = full_name_parts[0]
        last_name = full_name_parts[1] if len(full_name_parts) > 1 else ""

        return user_model.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_cart_context())
        context["checkout_step"] = 1
        return context


class CheckoutDeliveryView(CheckoutCartMixin, FormView):
    template_name = "shopapp/storefront/checkout_delivery.html"
    form_class = CheckoutDeliveryForm

    def dispatch(self, request, *args, **kwargs):
        self.checkout_session = CheckoutSession(request)

        if not self.checkout_session.get_step("customer"):
            messages.error(request, "Сначала заполните данные пользователя.")
            return redirect("shopapp:checkout_customer")

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return self.checkout_session.get_step("delivery").copy()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["cart_total"] = self.cart.total_price
        kwargs["shop_settings"] = ShopSettings.load()
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, "Проверьте способ доставки, город и адрес.")
        return super().form_invalid(form)

    def form_valid(self, form):
        delivery_data = form.cleaned_data.copy()
        delivery_data["delivery_price"] = str(
            ShopSettings.load().calculate_delivery_price(
                cart_total=self.cart.total_price,
                delivery_type=delivery_data["delivery_type"],
            )
        )
        self.checkout_session.update_step("delivery", delivery_data)
        return redirect("shopapp:checkout_payment")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_cart_context())
        context["checkout_step"] = 2
        context["shop_settings"] = ShopSettings.load()
        return context


class CheckoutPaymentView(CheckoutCartMixin, FormView):
    template_name = "shopapp/storefront/checkout_payment.html"
    form_class = CheckoutPaymentForm

    def dispatch(self, request, *args, **kwargs):
        self.checkout_session = CheckoutSession(request)

        if not self.checkout_session.get_step("customer"):
            messages.error(request, "Сначала заполните данные пользователя.")
            return redirect("shopapp:checkout_customer")

        if not self.checkout_session.get_step("delivery"):
            messages.error(request, "Сначала выберите способ доставки.")
            return redirect("shopapp:checkout_delivery")

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return self.checkout_session.get_step("payment").copy()

    def form_invalid(self, form):
        messages.error(self.request, "Выберите способ оплаты.")
        return super().form_invalid(form)

    def form_valid(self, form):
        self.checkout_session.update_step("payment", form.cleaned_data.copy())
        return redirect("shopapp:checkout_confirm")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_cart_context())
        context["checkout_step"] = 3
        return context


class CheckoutConfirmView(CheckoutCartMixin, FormView):
    template_name = "shopapp/storefront/checkout_confirm.html"
    form_class = CheckoutConfirmForm

    def dispatch(self, request, *args, **kwargs):
        self.checkout_session = CheckoutSession(request)

        if not self.checkout_session.get_step("customer"):
            messages.error(request, "Сначала заполните данные пользователя.")
            return redirect("shopapp:checkout_customer")

        if not self.checkout_session.get_step("delivery"):
            messages.error(request, "Сначала выберите способ доставки.")
            return redirect("shopapp:checkout_delivery")

        if not self.checkout_session.get_step("payment"):
            messages.error(request, "Сначала выберите способ оплаты.")
            return redirect("shopapp:checkout_payment")

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            "comment": self.checkout_session.get_step("confirm").get("comment", ""),
        }

    def form_valid(self, form):
        self.checkout_session.update_step("confirm", form.cleaned_data.copy())
        order = self.create_order_from_checkout()
        self.request.session["payment_order_id"] = order.pk
        self.request.session.modified = True
        messages.success(self.request, f"Заказ №{order.pk} создан. Теперь можно перейти к оплате.")
        return redirect("shopapp:layout_payment")

    @transaction.atomic
    def create_order_from_checkout(self) -> Order:
        state = self.checkout_session.get_state()
        customer = state["customer"]
        delivery = state["delivery"]
        payment = state["payment"]
        confirm = state.get("confirm", {})

        delivery_price = Decimal(str(delivery["delivery_price"]))
        items_price = self.cart.total_price
        total_price = items_price + delivery_price

        order = Order.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            full_name=customer["full_name"],
            email=customer["email"],
            phone=customer["phone"],
            city=delivery["city"],
            address=delivery["address"],
            delivery_address=f"{delivery['city']}, {delivery['address']}",
            delivery_type=delivery["delivery_type"],
            delivery_price=delivery_price,
            payment_type=payment["payment_type"],
            payment_status=Order.PaymentStatus.NOT_STARTED,
            comment=confirm.get("comment", ""),
            status="new",
            total_price_snapshot=total_price,
        )

        product_ids = []

        for cart_item in self.cart.items.select_related("product").all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name_snapshot=cart_item.product.name,
                quantity=cart_item.quantity,
                unit_price=cart_item.price_snapshot,
                total_price=cart_item.total_price,
            )
            product_ids.append(cart_item.product_id)

        order.products.set(product_ids)

        CartService(self.request).clear()
        self.checkout_session.clear()

        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        customer = self.checkout_session.get_step("customer")
        delivery = self.checkout_session.get_step("delivery")
        payment = self.checkout_session.get_step("payment")
        delivery_price = Decimal(str(delivery.get("delivery_price", "0")))

        context.update(self.get_cart_context())
        context["checkout_step"] = 4
        context["customer"] = customer
        context["delivery"] = delivery
        context["payment"] = payment
        context["delivery_price"] = delivery_price
        context["order_total_price"] = self.cart.total_price + delivery_price
        context["delivery_type_label"] = Order.DeliveryType(delivery["delivery_type"]).label
        context["payment_type_label"] = Order.PaymentType(payment["payment_type"]).label
        return context


class CheckoutStartRedirectView(View):
    def get(self, request, *args, **kwargs):
        return redirect("shopapp:checkout_customer")