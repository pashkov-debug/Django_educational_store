from urllib.parse import quote, unquote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.syndication.views import Feed
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, Prefetch, Q
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .cart import CartService, get_active_product_or_404
from .forms import OrderForm, ProductCatalogFilterForm, ProductForm
from .models import CartItem, Category, Manufacturer, Order, Product

LAYOUT_TEMPLATES = {
    "about": "shopapp/layout/about.html",
    "account": "shopapp/layout/account.html",
    "historyorder": "shopapp/layout/historyorder.html",
    "order": "shopapp/layout/order.html",
    "payment": "shopapp/layout/payment.html",
    "paymentsomeone": "shopapp/layout/paymentsomeone.html",
    "profile": "shopapp/layout/profile.html",
    "profileAvatar": "shopapp/layout/profileAvatar.html",
    "progressPayment": "shopapp/layout/progressPayment.html",
    "sale": "shopapp/layout/sale.html",
    "signIn": "shopapp/layout/signIn.html",
    "signUp": "shopapp/layout/signUp.html",
}

CHECKOUT_CITY_COOKIE_KEY = "checkout_city"
CHECKOUT_CITY_DEFAULT = "Город не выбран"
CHECKOUT_ADDRESS_SESSION_KEY = "checkout_delivery_address"
CHECKOUT_ADDRESS_DEFAULT = "Адрес не заполнен"


class LatestProductsFeed(Feed):
    title = "Последние товары магазина"
    description = "Пять последних активных товаров из каталога."

    def link(self):
        return reverse("shopapp:products_list")

    def items(self):
        return Product.objects.filter(archived=False).order_by("-created_at")[:5]

    def item_title(self, item: Product):
        return item.name

    def item_description(self, item: Product):
        return item.description

    def item_link(self, item: Product):
        return item.get_absolute_url()

    def item_pubdate(self, item: Product):
        return item.created_at


def _active_category_queryset():
    return (
        Category.objects.filter(archived=False, is_active=True)
        .prefetch_related(
            Prefetch(
                "children",
                queryset=Category.objects.filter(archived=False, is_active=True).order_by("sort_index", "name"),
                to_attr="active_menu_children",
            )
        )
        .order_by("sort_index", "name")
    )


def _catalog_queryset():
    return (
        Product.objects.filter(archived=False)
        .select_related("created_by", "category", "manufacturer")
        .prefetch_related("orders")
        .annotate(
            orders_count_value=Count(
                "orders",
                filter=Q(orders__archived=False),
                distinct=True,
            )
        )
    )


def _get_category_by_filter_value(value: str):
    if not value:
        return None

    query = Q(slug=value)
    if value.isdigit():
        query |= Q(pk=int(value))

    return Category.objects.filter(query, archived=False, is_active=True).first()


def _get_checkout_city(request) -> str:
    raw_value = request.COOKIES.get(CHECKOUT_CITY_COOKIE_KEY)
    if not raw_value:
        return CHECKOUT_CITY_DEFAULT
    return unquote(raw_value)


def _get_checkout_delivery_address(request) -> str:
    return request.session.get(CHECKOUT_ADDRESS_SESSION_KEY, CHECKOUT_ADDRESS_DEFAULT)


def _safe_redirect(request, fallback_url_name: str = "shopapp:layout_cart"):
    next_url = request.POST.get("next") or request.GET.get("next")

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect(fallback_url_name)


class LayoutPageView(TemplateView):
    layout_key = None

    def get_template_names(self):
        if self.layout_key not in LAYOUT_TEMPLATES:
            raise Http404("Страница не найдена")
        return [LAYOUT_TEMPLATES[self.layout_key]]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "layout_mode": True,
                "layout_page_key": self.layout_key,
            }
        )
        return context


class HomePageView(TemplateView):
    template_name = "shopapp/storefront/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_orders = (
            Order.objects.filter(archived=False)
            .select_related("user")
            .prefetch_related("products")
            .all()[:3]
        )
        popular_products = list(
            _catalog_queryset().order_by("sort_index", "-orders_count_value", "name")[:8]
        )
        limited_edition_products = list(
            _catalog_queryset().filter(is_limited_edition=True).order_by("sort_index", "name")[:16]
        )
        context.update(
            {
                "featured_categories": list(
                    _active_category_queryset().filter(parent__isnull=True, is_featured=True)[:3]
                ),
                "popular_products": popular_products,
                "limited_edition_products": limited_edition_products,
                "featured_products": popular_products[:4],
                "latest_orders": latest_orders,
            }
        )
        return context


class ProductActiveQuerysetMixin:
    def get_queryset(self):
        return _catalog_queryset()


class ProductAuthorAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        product = self.get_object()
        user = self.request.user
        if user.is_superuser:
            return True
        return user.has_perm("shopapp.change_product") and product.created_by_id == user.id


class ProductListView(ListView):
    model = Product
    template_name = "shopapp/storefront/catalog.html"
    context_object_name = "products"
    paginate_by = 9

    sort_options = (
        ("popular", "по популярности"),
        ("price", "по цене"),
        ("name", "по названию"),
        ("new", "по новизне"),
    )

    def get_filter_form(self):
        if not hasattr(self, "filter_form"):
            self.filter_form = ProductCatalogFilterForm(self.request.GET or None)
        return self.filter_form

    def get_queryset(self):
        queryset = _catalog_queryset()
        form = self.get_filter_form()

        if form.is_valid():
            data = form.cleaned_data
            search_query = data.get("q")
            category_value = data.get("category")
            manufacturer = data.get("manufacturer")
            price_min = data.get("price_min")
            price_max = data.get("price_max")
            sort = data.get("sort") or "name"
            direction = data.get("direction") or "asc"

            if search_query:
                queryset = queryset.filter(name__icontains=search_query)

            category = _get_category_by_filter_value(category_value)
            if category:
                category_ids = [category.pk]
                category_ids.extend(
                    category.children.filter(archived=False, is_active=True).values_list("pk", flat=True)
                )
                queryset = queryset.filter(category_id__in=category_ids)

            if manufacturer:
                queryset = queryset.filter(manufacturer=manufacturer)

            if price_min is not None:
                queryset = queryset.filter(price__gte=price_min)

            if price_max is not None:
                queryset = queryset.filter(price__lte=price_max)

            sort_map = {
                "popular": "orders_count_value",
                "price": "price",
                "name": "name",
                "new": "created_at",
            }
            sort_field = sort_map.get(sort, "name")
            if direction == "desc":
                sort_field = f"-{sort_field}"

            secondary_sort = "name" if sort_field.lstrip("-") != "name" else "pk"
            return queryset.order_by(sort_field, secondary_sort)

        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_category_value = self.request.GET.get("category", "")
        selected_category = _get_category_by_filter_value(selected_category_value)

        context.update(
            {
                "page_title": "Каталог товаров",
                "page_subtitle": "Каталог с фильтром по названию, категории, производителю, цене и сортировкой.",
                "catalog_items": context["products"],
                "filter_form": self.get_filter_form(),
                "categories": list(_active_category_queryset().filter(parent__isnull=True)),
                "manufacturers": Manufacturer.objects.filter(archived=False).order_by("name"),
                "selected_category": selected_category,
                "selected_category_value": selected_category_value,
                "sort_options": self.sort_options,
                "selected_sort": self.request.GET.get("sort", "name"),
                "selected_direction": self.request.GET.get("direction", "asc"),
                "query_without_page": self._query_without_page(),
            }
        )
        return context

    def _query_without_page(self):
        query = self.request.GET.copy()
        query.pop("page", None)
        encoded = query.urlencode()
        return f"{encoded}&" if encoded else ""


class ProductDetailView(ProductActiveQuerysetMixin, DetailView):
    template_name = "shopapp/storefront/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context.update(
            {
                "images_count": product.images_count,
                "related_orders": (
                    product.orders.filter(archived=False)
                    .select_related("user")
                    .prefetch_related("products")
                    .all()[:5]
                ),
            }
        )
        return context


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    permission_required = "shopapp.add_product"
    template_name = "shopapp/storefront/product_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Создание товара",
                "page_subtitle": "Добавление нового товара доступно только пользователям с правом shopapp.add_product.",
                "submit_label": "Создать товар",
                "cancel_url": reverse("shopapp:products_list"),
            }
        )
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Товар «{self.object.name}» успешно создан.")
        return response

    def get_success_url(self):
        return reverse("shopapp:product_detail", kwargs={"pk": self.object.pk})


class ProductUpdateView(ProductAuthorAccessMixin, ProductActiveQuerysetMixin, UpdateView):
    form_class = ProductForm
    template_name = "shopapp/storefront/product_form.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Редактирование товара «{self.object.name}»",
                "page_subtitle": "Суперпользователь редактирует всегда. Остальные — только свой товар и только с permission shopapp.change_product.",
                "submit_label": "Сохранить изменения",
                "cancel_url": reverse("shopapp:product_detail", kwargs={"pk": self.object.pk}),
            }
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Товар «{self.object.name}» успешно обновлён.")
        return response

    def get_success_url(self):
        return reverse("shopapp:product_detail", kwargs={"pk": self.object.pk})


class ProductArchiveView(ProductAuthorAccessMixin, ProductActiveQuerysetMixin, DeleteView):
    template_name = "shopapp/storefront/product_archive_confirm.html"
    context_object_name = "product"
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.archived = True
        self.object.save(update_fields=["archived"])
        messages.success(self.request, f"Товар «{self.object.name}» отправлен в архив.")
        return HttpResponseRedirect(self.get_success_url())


class CartDetailView(TemplateView):
    template_name = "shopapp/storefront/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = CartService(self.request).get_cart(create=False)

        if cart is None:
            items = CartItem.objects.none()
        else:
            items = cart.items.select_related("product", "product__category", "product__manufacturer").order_by("created_at", "pk")

        context.update(
            {
                "cart": cart,
                "cart_items": items,
                "cart_total_quantity": cart.total_quantity if cart else 0,
                "cart_total_price": cart.total_price if cart else 0,
            }
        )
        return context


class CartAddView(View):
    def post(self, request, product_id: int, *args, **kwargs):
        product = get_active_product_or_404(product_id)
        quantity = request.POST.get("quantity", 1)

        try:
            item = CartService(request).add_product(product, quantity=quantity)
        except ValueError as error:
            messages.error(request, str(error))
            return _safe_redirect(request, fallback_url_name="shopapp:products_list")

        messages.success(request, f"Товар «{item.product.name}» добавлен в корзину.")
        return _safe_redirect(request)


class CartItemUpdateView(View):
    def post(self, request, item_id: int, *args, **kwargs):
        quantity = request.POST.get("quantity", 1)

        try:
            item = CartService(request).update_item(item_id=item_id, quantity=quantity)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("shopapp:layout_cart")

        if item is None:
            messages.success(request, "Товар удалён из корзины.")
        else:
            messages.success(request, f"Количество товара «{item.product.name}» обновлено.")

        return redirect("shopapp:layout_cart")


class CartItemDeleteView(View):
    def post(self, request, item_id: int, *args, **kwargs):
        CartService(request).remove_item(item_id=item_id)
        messages.success(request, "Товар удалён из корзины.")
        return redirect("shopapp:layout_cart")


class OrderQuerysetMixin:
    def get_queryset(self):
        return Order.objects.filter(archived=False).select_related("user").prefetch_related("products")


class OrderListView(OrderQuerysetMixin, ListView):
    model = Order
    template_name = "shopapp/storefront/orders.html"
    context_object_name = "orders"

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")


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

        return str(order.pk) in {str(order_id) for order_id in session_order_ids if order_id}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        order_items = list(order.items.select_related("product").all())

        context.update(
            {
                "order_items": order_items,
                "products": [item.product for item in order_items] if order_items else list(order.products.all()),
                "products_count": order.products_count,
                "total_price": order.total_price,
            }
        )
        return context


class OrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = "shopapp/storefront/order_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Создание заказа",
                "page_subtitle": "Создание заказа с выбором пользователя и товаров через generic CreateView.",
                "submit_label": "Создать заказ",
                "cancel_url": reverse("shopapp:orders_list"),
            }
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Заказ №{self.object.pk} успешно создан.")
        return response

    def get_success_url(self):
        return reverse("shopapp:order_detail", kwargs={"pk": self.object.pk})


class OrderUpdateView(OrderQuerysetMixin, UpdateView):
    form_class = OrderForm
    template_name = "shopapp/storefront/order_form.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Редактирование заказа №{self.object.pk}",
                "page_subtitle": "Обновление заказа через generic UpdateView.",
                "submit_label": "Сохранить изменения",
                "cancel_url": reverse("shopapp:order_detail", kwargs={"pk": self.object.pk}),
            }
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Заказ №{self.object.pk} успешно обновлён.")
        return response

    def get_success_url(self):
        return reverse("shopapp:order_detail", kwargs={"pk": self.object.pk})


class OrderDeleteView(OrderQuerysetMixin, DeleteView):
    template_name = "shopapp/storefront/order_confirm_delete.html"
    context_object_name = "order"
    success_url = reverse_lazy("shopapp:orders_list")

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.archived = True
        self.object.save(update_fields=["archived"])
        messages.success(self.request, f"Заказ №{self.object.pk} отправлен в архив.")
        return HttpResponseRedirect(self.get_success_url())


@user_passes_test(lambda user: user.is_staff)
def orders_export_view(request):
    orders = (
        Order.objects.filter(archived=False)
        .select_related("user")
        .prefetch_related("products")
        .order_by("pk")
    )
    payload = {
        "orders": [
            {
                "id": order.pk,
                "delivery_address": order.delivery_address,
                "promo_code": order.promo_code,
                "user_id": order.user_id,
                "product_ids": list(order.products.values_list("pk", flat=True)),
            }
            for order in orders
        ]
    }
    return JsonResponse(payload)


class FileUploadView(View):
    template_name = "shopapp/storefront/upload.html"

    def _base_context(self):
        max_upload_size = getattr(settings, "MAX_UPLOAD_SIZE", 1024 * 1024)
        return {
            "max_upload_size_mb": round(max_upload_size / 1024 / 1024, 2),
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._base_context())

    def post(self, request, *args, **kwargs):
        max_upload_size = getattr(settings, "MAX_UPLOAD_SIZE", 1024 * 1024)
        context = self._base_context()
        uploaded_file = request.FILES.get("file")

        if uploaded_file is None:
            context["error"] = "Файл не выбран."
            return render(request, self.template_name, context, status=400)

        if uploaded_file.size > max_upload_size:
            context["error"] = "Размер файла не должен превышать 1 МБ."
            return render(request, self.template_name, context, status=400)

        storage = FileSystemStorage()
        saved_file_name = storage.save(uploaded_file.name, uploaded_file)

        context["success"] = "Файл успешно загружен."
        context["file_url"] = storage.url(saved_file_name)
        context["file_name"] = saved_file_name
        return render(request, self.template_name, context)


class CheckoutCityCookieReadView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"value": _get_checkout_city(request)})


class CheckoutCityCookieSetView(View):
    def post(self, request, *args, **kwargs):
        value = (request.POST.get("value") or CHECKOUT_CITY_DEFAULT).strip() or CHECKOUT_CITY_DEFAULT
        response = JsonResponse({"stored": value})
        response.set_cookie(
            CHECKOUT_CITY_COOKIE_KEY,
            quote(value),
            max_age=60 * 60 * 24 * 30,
            samesite="Lax",
        )
        return response


class CheckoutAddressSessionReadView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"value": _get_checkout_delivery_address(request)})


class CheckoutAddressSessionSetView(View):
    def post(self, request, *args, **kwargs):
        value = (request.POST.get("value") or CHECKOUT_ADDRESS_DEFAULT).strip() or CHECKOUT_ADDRESS_DEFAULT
        request.session[CHECKOUT_ADDRESS_SESSION_KEY] = value
        return JsonResponse({"stored": value})


class LayoutAboutView(LayoutPageView):
    layout_key = "about"


class LayoutAccountView(LayoutPageView):
    layout_key = "account"


class LayoutHistoryOrderView(LayoutPageView):
    layout_key = "historyorder"


class LayoutOrderView(LayoutPageView):
    layout_key = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["checkout_state"] = {
            "city": _get_checkout_city(self.request),
            "delivery_address": _get_checkout_delivery_address(self.request),
        }
        return context


class LayoutPaymentView(LayoutPageView):
    layout_key = "payment"


class LayoutPaymentSomeoneView(LayoutPageView):
    layout_key = "paymentsomeone"


class LayoutProfileView(LayoutPageView):
    layout_key = "profile"


class LayoutProfileAvatarView(LayoutPageView):
    layout_key = "profileAvatar"


class LayoutProgressPaymentView(LayoutPageView):
    layout_key = "progressPayment"


class LayoutSaleView(LayoutPageView):
    layout_key = "sale"


class LayoutSignUpView(LayoutPageView):
    layout_key = "signUp"