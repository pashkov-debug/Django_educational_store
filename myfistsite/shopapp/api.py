
import json
import random
from decimal import Decimal
from typing import Any

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.utils import timezone
from django.views import View

from accounts.models import Profile

from .models import Category, Order, OrderItem, Product, Review, ShopSettings


def _parse_body(request: HttpRequest) -> Any:
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            pass
    return request.POST.dict()


def _decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _image_payload(request: HttpRequest, product: Product) -> list[dict[str, str]]:
    if product.image:
        return [{"src": request.build_absolute_uri(product.image.url), "alt": product.name}]
    return [{"src": static("frontend/assets/img/content/home/card.jpg"), "alt": product.name}]


def _avatar_payload(request: HttpRequest, user) -> dict[str, str]:
    avatar_url = static("frontend/assets/img/icons/user_icon.svg")
    alt = user.username
    profile = getattr(user, "profile", None)
    if profile and profile.avatar:
        avatar_url = request.build_absolute_uri(profile.avatar.url)
    return {"src": avatar_url, "alt": alt}


def _format_datetime(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%d.%m.%Y %H:%M")


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _product_card_payload(request: HttpRequest, product: Product, *, count: int = 1) -> dict[str, Any]:
    return {
        "id": product.pk,
        "title": product.name,
        "price": float(product.final_price),
        "oldPrice": float(product.price),
        "salePrice": float(product.final_price),
        "shortDescription": product.short_description or product.description[:120],
        "description": product.description,
        "images": _image_payload(request, product),
        "category": product.category_id,
        "tags": [{"id": 1, "name": product.manufacturer}] if product.manufacturer else [],
        "specifications": [
            {"name": "Manufacturer", "value": product.manufacturer or "—"},
            {"name": "Category", "value": product.category.title if product.category else "General"},
            {"name": "Availability", "value": "In stock" if product.in_stock else "Out of stock"},
        ],
        "count": int(count),
        "href": f"/product/{product.pk}/",
        "reviewsCount": product.reviews_count,
    }


def _review_payload(review: Review) -> dict[str, Any]:
    return {
        "id": review.pk,
        "author": review.author,
        "email": review.email,
        "text": review.text,
        "rate": review.rate,
        "date": timezone.localtime(review.created_at).strftime("%d.%m.%Y"),
    }


def _order_payload(request: HttpRequest, order: Order) -> dict[str, Any]:
    items = list(order.items.select_related("product", "product__category"))
    products = [
        _product_card_payload(request, item.product, count=item.quantity)
        for item in items
    ]
    return {
        "id": order.pk,
        "createdAt": _format_datetime(order.created_at),
        "fullName": order.full_name,
        "phone": order.phone,
        "email": order.email,
        "deliveryType": dict(Order.DELIVERY_CHOICES).get(order.delivery_type, order.delivery_type),
        "city": order.city,
        "address": order.address,
        "paymentType": dict(Order.PAYMENT_CHOICES).get(order.payment_type, order.payment_type),
        "status": dict(Order.STATUS_CHOICES).get(order.status, order.status),
        "totalCost": float(order.grand_total),
        "subtotal": float(order.items_subtotal),
        "deliveryCost": float(order.delivery_cost),
        "products": products,
        "paymentError": order.payment_error or None,
        "comment": order.comment,
    }


def _category_payload(category: Category) -> dict[str, Any]:
    default_icon = static("frontend/assets/img/icons/departments/1.svg")
    children = [
        child for child in category.children.filter(is_active=True, archived=False).order_by("sort_index", "title")
    ]
    return {
        "id": category.pk,
        "title": category.title,
        "image": {"src": category.icon or default_icon, "alt": category.title},
        "subcategories": [
            {
                "id": child.pk,
                "title": child.title,
                "image": {"src": child.icon or default_icon, "alt": child.title},
            }
            for child in children[:12]
        ],
    }


def _get_basket(request: HttpRequest) -> dict[str, int]:
    basket = request.session.get("basket", {})
    if not isinstance(basket, dict):
        basket = {}
    normalized = {}
    for key, value in basket.items():
        quantity = _safe_int(value, 0)
        if quantity > 0:
            normalized[str(key)] = quantity
    request.session["basket"] = normalized
    return normalized


def _save_basket(request: HttpRequest, basket: dict[str, int]):
    request.session["basket"] = basket
    request.session.modified = True


class CategoriesApiView(View):
    def get(self, request, *args, **kwargs):
        categories = Category.objects.filter(parent__isnull=True, is_active=True, archived=False).prefetch_related(
            Prefetch("children", queryset=Category.objects.filter(is_active=True, archived=False))
        )
        return JsonResponse([_category_payload(category) for category in categories[:12]], safe=False)


class BasketApiView(View):
    def get(self, request, *args, **kwargs):
        basket = _get_basket(request)
        product_ids = [int(product_id) for product_id in basket.keys()]
        products = Product.objects.filter(pk__in=product_ids, archived=False).select_related("category")
        product_map = {product.pk: product for product in products}
        items = []
        for product_id, quantity in basket.items():
            product = product_map.get(int(product_id))
            if product:
                items.append(_product_card_payload(request, product, count=quantity))
        return JsonResponse(items, safe=False)

    def post(self, request, *args, **kwargs):
        payload = _parse_body(request)
        product_id = _safe_int(payload.get("id"))
        count = max(_safe_int(payload.get("count"), 1), 1)
        product = get_object_or_404(Product, pk=product_id, archived=False)
        basket = _get_basket(request)
        basket[str(product.pk)] = basket.get(str(product.pk), 0) + count
        _save_basket(request, basket)
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        payload = _parse_body(request)
        product_id = _safe_int(payload.get("id"))
        count = max(_safe_int(payload.get("count"), 1), 1)
        basket = _get_basket(request)
        key = str(product_id)
        if key in basket:
            basket[key] = basket[key] - count
            if basket[key] <= 0:
                basket.pop(key, None)
        _save_basket(request, basket)
        return self.get(request, *args, **kwargs)


class BannersApiView(View):
    def get(self, request, *args, **kwargs):
        products = Product.objects.filter(archived=False, in_stock=True).select_related("category").order_by("sort_index", "name")[:3]
        payload = []
        for product in products:
            item = _product_card_payload(request, product)
            payload.append(
                {
                    "title": item["title"],
                    "price": item["price"],
                    "images": item["images"],
                    "category": product.category_id or 0,
                }
            )
        return JsonResponse(payload, safe=False)


class PopularProductsApiView(View):
    def get(self, request, *args, **kwargs):
        products = (
            Product.objects.filter(archived=False)
            .select_related("category")
            .annotate(order_lines_count=Count("order_items", distinct=True))
            .order_by("sort_index", "-order_lines_count", "name")[:8]
        )
        return JsonResponse([_product_card_payload(request, product) for product in products], safe=False)


class LimitedProductsApiView(View):
    def get(self, request, *args, **kwargs):
        products = Product.objects.filter(archived=False, limited_edition=True).select_related("category").order_by("sort_index", "name")[:16]
        return JsonResponse([_product_card_payload(request, product) for product in products], safe=False)


class TagsApiView(View):
    def get(self, request, *args, **kwargs):
        category_id = _safe_int(request.GET.get("category")) or None
        queryset = Product.objects.filter(archived=False).exclude(manufacturer="")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        names = list(queryset.order_by("manufacturer").values_list("manufacturer", flat=True).distinct()[:20])
        return JsonResponse([{"id": index + 1, "name": name} for index, name in enumerate(names)], safe=False)


class CatalogApiView(View):
    def get(self, request, *args, **kwargs):
        filter_payload = request.GET.get("filter")
        if isinstance(filter_payload, str):
            try:
                filter_payload = json.loads(filter_payload)
            except json.JSONDecodeError:
                filter_payload = None

        if filter_payload is None:
            filter_payload = {}

        current_page = _safe_int(request.GET.get("currentPage"), 1)
        category_id = _safe_int(request.GET.get("category")) or None
        sort = request.GET.get("sort") or "price"
        sort_type = request.GET.get("sortType") or "inc"

        products = Product.objects.filter(archived=False).select_related("category").annotate(
            order_lines_count=Count("order_items", distinct=True),
            reviews_total=Count("reviews", filter=Q(reviews__is_active=True), distinct=True),
        )

        if category_id:
            products = products.filter(Q(category_id=category_id) | Q(category__parent_id=category_id))

        name_filter = (filter_payload.get("name") or request.GET.get("filter") or "").strip()
        if name_filter and not isinstance(filter_payload, str):
            products = products.filter(name__icontains=name_filter)

        min_price = filter_payload.get("minPrice")
        max_price = filter_payload.get("maxPrice")
        try:
            if min_price not in (None, "", "0"):
                products = products.filter(price__gte=Decimal(str(min_price)))
            if max_price not in (None, "", "0"):
                products = products.filter(price__lte=Decimal(str(max_price)))
        except Exception:
            pass

        available = filter_payload.get("available")
        if available in (True, "true", "True", "1"):
            products = products.filter(in_stock=True)

        tags = request.GET.getlist("tags") or []
        if not tags:
            raw_tags = request.GET.get("tags")
            if raw_tags:
                try:
                    tags = json.loads(raw_tags)
                except Exception:
                    tags = []
        if tags:
            manufacturers = list(
                Product.objects.filter(archived=False)
                .exclude(manufacturer="")
                .order_by("manufacturer")
                .values_list("manufacturer", flat=True)
                .distinct()
            )
            selected_names = []
            for tag_id in tags:
                index = _safe_int(tag_id) - 1
                if 0 <= index < len(manufacturers):
                    selected_names.append(manufacturers[index])
            if selected_names:
                products = products.filter(manufacturer__in=selected_names)

        ordering_map = {
            "rating": "-order_lines_count" if sort_type == "dec" else "order_lines_count",
            "price": "-price" if sort_type == "dec" else "price",
            "reviews": "-reviews_total" if sort_type == "dec" else "reviews_total",
            "date": "-created_at" if sort_type == "dec" else "created_at",
        }
        ordering = ordering_map.get(sort, "price")
        products = products.order_by(ordering, "name")

        paginator = Paginator(products, 20)
        page = paginator.get_page(current_page)
        return JsonResponse(
            {
                "items": [_product_card_payload(request, product) for product in page.object_list],
                "currentPage": page.number,
                "lastPage": paginator.num_pages or 1,
            }
        )


class ProductApiView(View):
    def get(self, request, product_id: int, *args, **kwargs):
        product = get_object_or_404(
            Product.objects.filter(archived=False).select_related("category").annotate(
                reviews_total=Count("reviews", filter=Q(reviews__is_active=True), distinct=True)
            ),
            pk=product_id,
        )
        payload = _product_card_payload(request, product)
        payload["reviews"] = [_review_payload(review) for review in product.reviews.filter(is_active=True)[:20]]
        payload["specification"] = payload["specifications"]
        return JsonResponse(payload)


class ProductReviewsApiView(View):
    def post(self, request, product_id: int, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=403)

        product = get_object_or_404(Product, pk=product_id, archived=False)
        payload = _parse_body(request)
        author = (payload.get("author") or getattr(request.user, "get_full_name", lambda: "")() or request.user.username).strip()
        email = (payload.get("email") or request.user.email or "").strip()
        text = (payload.get("text") or "").strip()
        rate = _safe_int(payload.get("rate"), 5)

        if not text:
            return JsonResponse({"error": "Review text is required."}, status=400)
        rate = min(max(rate, 1), 5)

        Review.objects.create(
            product=product,
            user=request.user,
            author=author or request.user.username,
            email=email,
            text=text,
            rate=rate,
        )
        reviews = [_review_payload(review) for review in product.reviews.filter(is_active=True)[:20]]
        return JsonResponse(reviews, safe=False)


class OrdersApiView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse([], safe=False)
        orders = Order.objects.filter(user=request.user, archived=False).prefetch_related("items__product", "items__product__category").order_by("-created_at")
        return JsonResponse([_order_payload(request, order) for order in orders], safe=False)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        basket = _get_basket(request)
        if not basket:
            return JsonResponse({"error": "Basket is empty."}, status=400)

        product_ids = [int(product_id) for product_id in basket.keys()]
        products = Product.objects.filter(pk__in=product_ids, archived=False)
        product_map = {product.pk: product for product in products}
        if len(product_map) != len(product_ids):
            return JsonResponse({"error": "One or more products were not found."}, status=400)

        profile = None
        if request.user.is_authenticated:
            profile, _ = Profile.objects.get_or_create(user=request.user)

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=getattr(profile, "full_name", "") if profile else "",
            phone=getattr(profile, "phone", "") if profile else "",
            email=request.user.email if request.user.is_authenticated else "",
            city="",
            address="",
            delivery_type=Order.DELIVERY_REGULAR,
            payment_type=Order.PAYMENT_CARD,
            status=Order.STATUS_DRAFT,
        )

        for product_id, quantity in basket.items():
            product = product_map[int(product_id)]
            order.products.add(product)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=max(_safe_int(quantity, 1), 1),
                price_snapshot=product.final_price,
            )

        return JsonResponse({"orderId": order.pk})


class OrderApiView(View):
    def _get_order(self, request, order_id: int) -> Order:
        queryset = Order.objects.filter(pk=order_id, archived=False).prefetch_related("items__product", "items__product__category")
        if request.user.is_authenticated:
            queryset = queryset.filter(Q(user=request.user) | Q(user__isnull=True))
        return get_object_or_404(queryset)

    def get(self, request, order_id: int, *args, **kwargs):
        order = self._get_order(request, order_id)
        return JsonResponse(_order_payload(request, order))

    @transaction.atomic
    def post(self, request, order_id: int, *args, **kwargs):
        order = self._get_order(request, order_id)
        payload = _parse_body(request)

        full_name = (payload.get("fullName") or "").strip()
        phone = (payload.get("phone") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        delivery_type = (payload.get("deliveryType") or Order.DELIVERY_REGULAR).strip()
        city = (payload.get("city") or "").strip()
        address = (payload.get("address") or "").strip()
        payment_type = (payload.get("paymentType") or Order.PAYMENT_CARD).strip()
        comment = (payload.get("comment") or "").strip()

        if not full_name or not email:
            return JsonResponse({"error": "Full name and email are required."}, status=400)
        if not city or not address:
            return JsonResponse({"error": "City and address are required."}, status=400)

        if delivery_type not in dict(Order.DELIVERY_CHOICES):
            delivery_type = Order.DELIVERY_REGULAR
        if payment_type not in dict(Order.PAYMENT_CHOICES):
            payment_type = Order.PAYMENT_CARD

        if request.user.is_authenticated:
            order.user = request.user
            profile, _ = Profile.objects.get_or_create(user=request.user)
            profile.full_name = full_name
            profile.phone = phone
            profile.save(update_fields=["full_name", "phone", "updated_at"])
            if request.user.email != email:
                request.user.email = email
                request.user.save(update_fields=["email"])
        else:
            existing_user = get_user_model().objects.filter(email__iexact=email).first()
            if existing_user:
                return JsonResponse({"error": "User with this email already exists. Please sign in."}, status=400)

        order.full_name = full_name
        order.phone = phone
        order.email = email
        order.delivery_type = delivery_type
        order.city = city
        order.address = address
        order.payment_type = payment_type
        order.comment = comment
        order.status = Order.STATUS_NEW
        order.sync_delivery_address()
        order.save()

        return JsonResponse({"orderId": order.pk})


class PaymentApiView(View):
    def post(self, request, order_id: int, *args, **kwargs):
        order = get_object_or_404(Order.objects.filter(archived=False), pk=order_id)
        if request.user.is_authenticated and order.user and order.user_id != request.user.id:
            return JsonResponse({"error": "Order does not belong to current user."}, status=403)

        payload = _parse_body(request)
        number = "".join(ch for ch in str(payload.get("number") or "") if ch.isdigit())[:8]
        if not number:
            return JsonResponse({"error": "Payment number is required."}, status=400)
        if len(number) > 8:
            return JsonResponse({"error": "Payment number is too long."}, status=400)

        if int(number) % 2 != 0:
            order.payment_error = "Payment service rejected odd number."
            order.status = Order.STATUS_PAYMENT_ERROR
            order.payment_number = number
            order.payment_attempted_at = timezone.now()
            order.save(update_fields=["payment_error", "status", "payment_number", "payment_attempted_at"])
            return JsonResponse({"error": order.payment_error}, status=400)

        if number.endswith("0"):
            order.payment_error = "Payment service returned random processing error."
            order.status = Order.STATUS_PAYMENT_ERROR
            order.payment_number = number
            order.payment_attempted_at = timezone.now()
            order.save(update_fields=["payment_error", "status", "payment_number", "payment_attempted_at"])
            return JsonResponse({"error": order.payment_error}, status=400)

        order.payment_error = ""
        order.status = Order.STATUS_PAID
        order.payment_number = number
        order.payment_attempted_at = timezone.now()
        order.save(update_fields=["payment_error", "status", "payment_number", "payment_attempted_at"])
        _save_basket(request, {})
        return JsonResponse({"message": "Waiting for payment system confirmation."})


class SalesApiView(View):
    def get(self, request, *args, **kwargs):
        current_page = _safe_int(request.GET.get("currentPage"), 1)
        products = Product.objects.filter(archived=False, discount__gt=0).select_related("category").order_by("-discount", "name")
        paginator = Paginator(products, 12)
        page = paginator.get_page(current_page)
        items = []
        for product in page.object_list:
            card = _product_card_payload(request, product)
            card["dateFrom"] = timezone.now().strftime("%d")
            card["dateTo"] = (timezone.now() + timezone.timedelta(days=10)).strftime("%d")
            items.append(card)
        return JsonResponse({"items": items, "currentPage": page.number, "lastPage": paginator.num_pages or 1})


class ProfileApiView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=403)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return JsonResponse(
            {
                "fullName": profile.full_name or request.user.get_full_name() or request.user.username,
                "phone": profile.phone,
                "email": request.user.email,
                "avatar": _avatar_payload(request, request.user),
            }
        )

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=403)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        payload = _parse_body(request)
        full_name = (payload.get("fullName") or "").strip()
        phone = (payload.get("phone") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        if not full_name or not email:
            return JsonResponse({"error": "Full name and email are required."}, status=400)
        if get_user_model().objects.exclude(pk=request.user.pk).filter(email__iexact=email).exists():
            return JsonResponse({"error": "Email already exists."}, status=400)
        request.user.email = email
        request.user.save(update_fields=["email"])
        profile.full_name = full_name
        profile.phone = phone
        profile.save(update_fields=["full_name", "phone", "updated_at"])
        return self.get(request, *args, **kwargs)


class ProfilePasswordApiView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=403)
        payload = _parse_body(request)
        current_password = payload.get("currentPassword") or ""
        password = payload.get("password") or ""
        password_reply = payload.get("passwordReply") or ""
        if not request.user.check_password(current_password):
            return JsonResponse({"error": "Current password is invalid."}, status=400)
        if password != password_reply:
            return JsonResponse({"error": "Passwords do not match."}, status=400)
        try:
            validate_password(password, request.user)
        except Exception as error:
            messages = [str(message) for message in getattr(error, "messages", [str(error)])]
            return JsonResponse({"error": " ".join(messages)}, status=400)
        request.user.set_password(password)
        request.user.save(update_fields=["password"])
        login(request, request.user)
        return JsonResponse({"ok": True})


class ProfileAvatarApiView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=403)
        avatar = request.FILES.get("avatar")
        if not avatar:
            return JsonResponse({"error": "Avatar file is required."}, status=400)
        if avatar.size > 2 * 1024 * 1024:
            return JsonResponse({"error": "Avatar must be 2 MB or smaller."}, status=400)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.avatar = avatar
        profile.save(update_fields=["avatar", "updated_at"])
        return JsonResponse(_avatar_payload(request, request.user))


class AccountApiView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=403)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        full_name = profile.full_name or request.user.get_full_name() or request.user.username
        parts = [part for part in full_name.split() if part]
        surname = parts[0] if parts else request.user.username
        firstname = parts[1] if len(parts) > 1 else ""
        secondname = " ".join(parts[2:]) if len(parts) > 2 else ""
        latest_orders = Order.objects.filter(user=request.user, archived=False).prefetch_related("items__product", "items__product__category").order_by("-created_at")[:2]
        return JsonResponse(
            {
                "surname": surname,
                "firstname": firstname,
                "secondname": secondname,
                "avatar": _avatar_payload(request, request.user),
                "orders": [_order_payload(request, order) for order in latest_orders],
            }
        )


class SignInApiView(View):
    def post(self, request, *args, **kwargs):
        payload = _parse_body(request)
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if not user:
            return JsonResponse({"error": "Invalid credentials."}, status=400)
        login(request, user)
        return JsonResponse({"ok": True})


class SignUpApiView(View):
    def post(self, request, *args, **kwargs):
        payload = _parse_body(request)
        name = (payload.get("name") or "").strip()
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        if not username or not password:
            return JsonResponse({"error": "Username and password are required."}, status=400)
        user_model = get_user_model()
        if user_model.objects.filter(username__iexact=username).exists():
            return JsonResponse({"error": "Username already exists."}, status=400)
        try:
            validate_password(password)
        except Exception as error:
            messages = [str(message) for message in getattr(error, "messages", [str(error)])]
            return JsonResponse({"error": " ".join(messages)}, status=400)
        user = user_model.objects.create_user(username=username, password=password)
        if name:
            Profile.objects.update_or_create(user=user, defaults={"full_name": name})
        login(request, user)
        return JsonResponse({"ok": True})


class SignOutApiView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return JsonResponse({"ok": True})
