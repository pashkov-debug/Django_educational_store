import secrets

from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import FormView, TemplateView

from .models import Order, Payment


class PaymentAccountForm(forms.Form):
    account_number = forms.CharField(
        label="Номер счёта или карты",
        max_length=8,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Например, 22222222",
                "inputmode": "numeric",
                "maxlength": "8",
                "style": "display: block; width: 100%; max-width: 360px; height: 44px; padding: 8px 12px; border: 1px solid #999;",
            }
        ),
    )

    def clean_account_number(self):
        value = self.cleaned_data["account_number"].strip()

        if not value.isdigit():
            raise forms.ValidationError("Номер должен содержать только цифры.")

        if len(value) > 8:
            raise forms.ValidationError("Номер должен быть не длиннее 8 цифр.")

        return value


class PaymentOrderMixin:
    def get_payable_order(self):
        order_id = self.request.session.get("payment_order_id")

        queryset = Order.objects.filter(
            archived=False,
            payment_status__in=[
                Order.PaymentStatus.NOT_STARTED,
                Order.PaymentStatus.PENDING,
                Order.PaymentStatus.FAILED,
            ],
        ).prefetch_related("items", "products")

        if order_id:
            order = queryset.filter(pk=order_id).first()
            if order:
                return order

        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user).order_by("-created_at").first()

        return None

    def create_pending_payment(self, *, order: Order, account_number: str) -> Payment:
        pending_payment = order.payments.filter(status=Payment.Status.PENDING).order_by("-created_at").first()

        if pending_payment:
            return pending_payment

        payment = Payment.objects.create(
            order=order,
            account_number=account_number,
            amount=order.total_price,
            status=Payment.Status.PENDING,
        )

        order.payment_status = Order.PaymentStatus.PENDING
        order.payment_error = ""
        order.status = "payment_pending"
        order.save(update_fields=("payment_status", "payment_error", "status"))

        self.request.session["payment_order_id"] = order.pk
        self.request.session["payment_id"] = payment.pk
        self.request.session.modified = True

        return payment


class PaymentPageView(PaymentOrderMixin, FormView):
    template_name = "shopapp/storefront/payment.html"
    form_class = PaymentAccountForm

    def dispatch(self, request, *args, **kwargs):
        self.order = self.get_payable_order()

        if self.order is None:
            messages.error(request, "Не найден заказ для оплаты.")
            return redirect("shopapp:orders_list")

        pending_payment = self.order.payments.filter(status=Payment.Status.PENDING).order_by("-created_at").first()
        if pending_payment:
            request.session["payment_id"] = pending_payment.pk
            request.session["payment_order_id"] = self.order.pk
            request.session.modified = True
            messages.info(request, "Платёж уже ожидает обработки.")
            return redirect("shopapp:layout_progress_payment")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        payment = self.create_pending_payment(
            order=self.order,
            account_number=form.cleaned_data["account_number"],
        )
        messages.success(self.request, f"Платёж №{payment.pk} создан и ожидает обработки.")
        return redirect("shopapp:layout_progress_payment")

    def form_invalid(self, form):
        messages.error(self.request, "Проверьте номер счёта или карты.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        context["order_items"] = self.order.items.select_related("product").all()
        context["payment_status_label"] = self.order.payment_status_label
        return context


class PaymentSomeoneView(PaymentOrderMixin, TemplateView):
    template_name = "shopapp/storefront/payment_someone.html"

    def dispatch(self, request, *args, **kwargs):
        self.order = self.get_payable_order()

        if self.order is None:
            messages.error(request, "Не найден заказ для оплаты.")
            return redirect("shopapp:orders_list")

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        account_number = self.generate_random_account_number()
        payment = self.create_pending_payment(order=self.order, account_number=account_number)

        messages.success(
            request,
            f"Создан платёж №{payment.pk} со случайного счёта {payment.account_number}.",
        )
        return redirect("shopapp:layout_progress_payment")

    def generate_random_account_number(self) -> str:
        return str(secrets.randbelow(90_000_000) + 10_000_000)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context


class PaymentProgressView(TemplateView):
    template_name = "shopapp/storefront/progress_payment.html"

    def dispatch(self, request, *args, **kwargs):
        self.payment = self.get_payment()

        if self.payment is None:
            messages.error(request, "Платёж не найден.")
            return redirect("shopapp:orders_list")

        self.sync_session_after_processed_payment()

        return super().dispatch(request, *args, **kwargs)

    def get_payment(self):
        payment_id = self.request.session.get("payment_id")

        queryset = Payment.objects.select_related("order").prefetch_related("order__items", "order__items__product")

        if payment_id:
            payment = queryset.filter(pk=payment_id).first()
            if payment:
                return payment

        order_id = self.request.session.get("payment_order_id")
        if order_id:
            payment = queryset.filter(order_id=order_id).order_by("-created_at").first()
            if payment:
                return payment

        if self.request.user.is_authenticated:
            return queryset.filter(order__user=self.request.user).order_by("-created_at").first()

        return None

    def sync_session_after_processed_payment(self):
        if self.payment.status == Payment.Status.PAID:
            self.request.session["last_paid_order_id"] = self.payment.order_id
            self.request.session.pop("payment_order_id", None)
            self.request.session.modified = True

        if self.payment.status == Payment.Status.FAILED:
            self.request.session["payment_order_id"] = self.payment.order_id
            self.request.session.modified = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment"] = self.payment
        context["order"] = self.payment.order
        context["order_items"] = self.payment.order.items.select_related("product").all()
        return context


class PaymentRetryView(View):
    def post(self, request, order_id: int, *args, **kwargs):
        order = Order.objects.filter(pk=order_id, archived=False).first()

        if order is None:
            messages.error(request, "Заказ не найден.")
            return redirect("shopapp:orders_list")

        if request.user.is_authenticated and order.user_id and order.user_id != request.user.id and not request.user.is_staff:
            messages.error(request, "Нет доступа к этому заказу.")
            return redirect("shopapp:orders_list")

        request.session["payment_order_id"] = order.pk
        request.session.pop("payment_id", None)
        request.session.modified = True

        return redirect("shopapp:layout_payment")