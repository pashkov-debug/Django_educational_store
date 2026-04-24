from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import OrderViewSet, ProductViewSet
from .checkout import (
    CheckoutConfirmView,
    CheckoutCustomerView,
    CheckoutDeliveryView,
    CheckoutPaymentView,
    CheckoutStartRedirectView,
)
from .content_pages import (
    AboutPageView,
    LegacyAccountRedirectView,
    LegacyProfileAvatarRedirectView,
    LegacyProfileRedirectView,
    SalePageView,
)
from .order_history import UserOrderHistoryView
from .payment import PaymentPageView, PaymentProgressView, PaymentRetryView, PaymentSomeoneView
from .views import (
    CartAddView,
    CartDetailView,
    CartItemDeleteView,
    CartItemUpdateView,
    CheckoutAddressSessionReadView,
    CheckoutAddressSessionSetView,
    CheckoutCityCookieReadView,
    CheckoutCityCookieSetView,
    FileUploadView,
    HomePageView,
    LatestProductsFeed,
    OrderCreateView,
    OrderDeleteView,
    OrderDetailView,
    orders_export_view,
    OrderListView,
    OrderUpdateView,
    ProductArchiveView,
    ProductCreateView,
    ProductDetailView,
    ProductListView,
    ProductUpdateView,
)

app_name = "shopapp"

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", HomePageView.as_view(), name="index"),
    path("api/", include(router.urls)),
    path("checkout/state/city/", CheckoutCityCookieReadView.as_view(), name="checkout_city_read"),
    path("checkout/state/city/set/", CheckoutCityCookieSetView.as_view(), name="checkout_city_set"),
    path("checkout/state/address/", CheckoutAddressSessionReadView.as_view(), name="checkout_address_read"),
    path("checkout/state/address/set/", CheckoutAddressSessionSetView.as_view(), name="checkout_address_set"),
    path("checkout/", CheckoutStartRedirectView.as_view(), name="checkout_start"),
    path("checkout/customer/", CheckoutCustomerView.as_view(), name="checkout_customer"),
    path("checkout/delivery/", CheckoutDeliveryView.as_view(), name="checkout_delivery"),
    path("checkout/payment/", CheckoutPaymentView.as_view(), name="checkout_payment"),
    path("checkout/confirm/", CheckoutConfirmView.as_view(), name="checkout_confirm"),
    path("products/latest/feed/", LatestProductsFeed(), name="products_latest_feed"),
    path("catalog/", ProductListView.as_view(), name="products_list"),
    path("catalog/", ProductListView.as_view(), name="catalog"),
    path("catalog/create/", ProductCreateView.as_view(), name="product_create"),
    path("catalog/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("catalog/<int:pk>/update/", ProductUpdateView.as_view(), name="product_update"),
    path("catalog/<int:pk>/archive/", ProductArchiveView.as_view(), name="product_archive"),
    path("cart/", CartDetailView.as_view(), name="layout_cart"),
    path("cart/", CartDetailView.as_view(), name="cart_detail"),
    path("cart/add/<int:product_id>/", CartAddView.as_view(), name="cart_add"),
    path("cart/items/<int:item_id>/update/", CartItemUpdateView.as_view(), name="cart_item_update"),
    path("cart/items/<int:item_id>/delete/", CartItemDeleteView.as_view(), name="cart_item_delete"),
    path("orders/", OrderListView.as_view(), name="orders_list"),
    path("orders/", OrderListView.as_view(), name="orders"),
    path("orders/create/", OrderCreateView.as_view(), name="order_create"),
    path("orders/export/", orders_export_view, name="orders_export"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path("orders/<int:pk>/update/", OrderUpdateView.as_view(), name="order_update"),
    path("orders/<int:pk>/delete/", OrderDeleteView.as_view(), name="order_delete"),
    path("orders/<int:order_id>/payment/retry/", PaymentRetryView.as_view(), name="payment_retry"),
    path("upload/", FileUploadView.as_view(), name="upload_file"),
    path("about/", AboutPageView.as_view(), name="layout_about"),
    path("account/", LegacyAccountRedirectView.as_view(), name="layout_account"),
    path("history-order/", UserOrderHistoryView.as_view(), name="layout_history_order"),
    path("order/", CheckoutStartRedirectView.as_view(), name="layout_order"),
    path("payment/", PaymentPageView.as_view(), name="layout_payment"),
    path("paymentsomeone/", PaymentSomeoneView.as_view(), name="layout_payment_someone"),
    path("progress-payment/", PaymentProgressView.as_view(), name="layout_progress_payment"),
    path("profile/", LegacyProfileRedirectView.as_view(), name="layout_profile"),
    path("profile/avatar/", LegacyProfileAvatarRedirectView.as_view(), name="layout_profile_avatar"),
    path("sale/", SalePageView.as_view(), name="layout_sale"),
]