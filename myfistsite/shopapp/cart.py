from decimal import Decimal, ROUND_HALF_UP

from django.http import Http404
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem, Product


MONEY_QUANT = Decimal("0.01")


def normalize_money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


class CartService:
    def __init__(self, request):
        self.request = request

    def get_cart(self, *, create: bool = True) -> Cart | None:
        if self.request.user.is_authenticated:
            return self._get_user_cart(create=create)

        return self._get_session_cart(create=create)

    def add_product(self, product: Product, quantity: int = 1) -> CartItem:
        quantity = self._normalize_quantity(quantity)
        cart = self.get_cart(create=True)
        price_snapshot = normalize_money(product.final_price)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "quantity": quantity,
                "price_snapshot": price_snapshot,
            },
        )

        if not created:
            item.quantity += quantity
            item.save(update_fields=("quantity", "updated_at"))

        cart.save(update_fields=("updated_at",))
        return item

    def update_item(self, item_id: int, quantity: int) -> CartItem | None:
        quantity = self._normalize_quantity(quantity, allow_zero=True)
        cart = self.get_cart(create=False)

        if cart is None:
            raise Http404("Корзина не найдена.")

        item = get_object_or_404(CartItem, pk=item_id, cart=cart)

        if quantity == 0:
            item.delete()
            cart.save(update_fields=("updated_at",))
            return None

        item.quantity = quantity
        item.save(update_fields=("quantity", "updated_at"))
        cart.save(update_fields=("updated_at",))
        return item

    def remove_item(self, item_id: int) -> None:
        cart = self.get_cart(create=False)

        if cart is None:
            raise Http404("Корзина не найдена.")

        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        item.delete()
        cart.save(update_fields=("updated_at",))

    def clear(self) -> None:
        cart = self.get_cart(create=False)
        if cart is None:
            return

        cart.items.all().delete()
        cart.save(update_fields=("updated_at",))

    def get_total_quantity(self) -> int:
        cart = self.get_cart(create=False)
        if cart is None:
            return 0

        return cart.total_quantity

    def get_total_price(self) -> Decimal:
        cart = self.get_cart(create=False)
        if cart is None:
            return Decimal("0")

        return cart.total_price

    def _get_user_cart(self, *, create: bool) -> Cart | None:
        user_cart = Cart.objects.filter(
            user=self.request.user,
            is_active=True,
        ).first()

        if user_cart:
            self._merge_session_cart_into_user_cart(user_cart)
            return user_cart

        if not create:
            return None

        user_cart = Cart.objects.create(user=self.request.user, is_active=True)
        self._merge_session_cart_into_user_cart(user_cart)
        return user_cart

    def _get_session_cart(self, *, create: bool) -> Cart | None:
        session_key = self._get_or_create_session_key(create=create)

        if not session_key:
            return None

        cart = Cart.objects.filter(
            user__isnull=True,
            session_key=session_key,
            is_active=True,
        ).first()

        if cart:
            return cart

        if not create:
            return None

        return Cart.objects.create(
            session_key=session_key,
            is_active=True,
        )

    def _merge_session_cart_into_user_cart(self, user_cart: Cart) -> None:
        session_key = self.request.session.session_key

        if not session_key:
            return

        guest_cart = (
            Cart.objects.filter(
                user__isnull=True,
                session_key=session_key,
                is_active=True,
            )
            .exclude(pk=user_cart.pk)
            .prefetch_related("items")
            .first()
        )

        if guest_cart is None:
            return

        for guest_item in guest_cart.items.select_related("product"):
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=guest_item.product,
                defaults={
                    "quantity": guest_item.quantity,
                    "price_snapshot": normalize_money(guest_item.price_snapshot),
                },
            )

            if not created:
                user_item.quantity += guest_item.quantity
                user_item.save(update_fields=("quantity", "updated_at"))

        guest_cart.is_active = False
        guest_cart.save(update_fields=("is_active", "updated_at"))
        user_cart.save(update_fields=("updated_at",))

    def _get_or_create_session_key(self, *, create: bool) -> str:
        session_key = self.request.session.session_key

        if session_key:
            return session_key

        if not create:
            return ""

        self.request.session.save()
        return self.request.session.session_key or ""

    def _normalize_quantity(self, value, *, allow_zero: bool = False) -> int:
        try:
            quantity = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Количество должно быть числом.") from error

        min_value = 0 if allow_zero else 1

        if quantity < min_value:
            raise ValueError("Количество должно быть больше нуля.")

        return quantity


def get_active_product_or_404(product_id: int) -> Product:
    return get_object_or_404(Product, pk=product_id, archived=False)