
import csv
from io import StringIO

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import OrderImportForm
from .models import Category, Order, OrderItem, Product, Review, ShopSettings


class SoftDeleteAdminMixin:
    archive_field_name = "archived"

    def delete_model(self, request, obj):
        if hasattr(obj, self.archive_field_name):
            setattr(obj, self.archive_field_name, True)
            obj.save(update_fields=[self.archive_field_name])
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.model and hasattr(queryset.model, self.archive_field_name):
            queryset.update(**{self.archive_field_name: True})
            return
        super().delete_queryset(request, queryset)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if hasattr(self.model, self.archive_field_name):
            actions.pop("delete_selected", None)
        return actions


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ("author", "email", "rate", "text", "created_at", "is_active")
    readonly_fields = ("created_at",)


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("pk", "title", "parent", "sort_index", "is_active", "archived")
    list_filter = ("is_active", "archived")
    search_fields = ("title", "slug")
    autocomplete_fields = ("parent",)


@admin.register(Product)
class ProductAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "category",
        "manufacturer",
        "price",
        "discount",
        "final_price_display",
        "limited_edition",
        "in_stock",
        "archived",
    )
    list_filter = ("archived", "limited_edition", "in_stock", "category")
    search_fields = ("name", "description", "short_description", "manufacturer")
    readonly_fields = ("image_preview",)
    autocomplete_fields = ("category", "created_by")
    inlines = (ReviewInline,)

    fieldsets = (
        (None, {"fields": ("category", "name", "short_description", "description", "manufacturer")}),
        ("Media", {"fields": ("image", "image_preview")}),
        ("Pricing", {"fields": ("price", "discount", "sort_index")}),
        ("State", {"fields": ("limited_edition", "in_stock", "archived", "created_by")}),
    )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="max-height:80px;border-radius:8px;" alt="{}"/>', obj.image.url, obj.name)

    @admin.display(description="Final price")
    def final_price_display(self, obj):
        return obj.final_price


@admin.register(Order)
class OrderAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    change_list_template = "shopapp/orders_changelist.html"
    list_display = (
        "pk",
        "full_name",
        "status",
        "payment_type",
        "delivery_type",
        "grand_total_display",
        "user",
        "created_at",
        "archived",
    )
    list_filter = ("archived", "status", "payment_type", "delivery_type", "created_at")
    search_fields = ("full_name", "email", "phone", "city", "address", "user__username")
    autocomplete_fields = ("user", "products")
    inlines = (OrderItemInline,)

    fieldsets = (
        ("Client", {"fields": ("user", "full_name", "email", "phone")}),
        ("Delivery", {"fields": ("city", "address", "delivery_type", "delivery_address")}),
        ("Payment", {"fields": ("payment_type", "payment_number", "payment_error")}),
        ("State", {"fields": ("status", "promo_code", "comment", "archived")}),
        ("Products", {"fields": ("products",)}),
    )

    @admin.display(description="Grand total")
    def grand_total_display(self, obj):
        return obj.grand_total

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv),
                name="shopapp_order_import_csv",
            ),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = OrderImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    created_orders = self._import_orders_from_csv(form.cleaned_data["csv_file"])
                except ValueError as error:
                    self.message_user(request, str(error), level=messages.ERROR)
                else:
                    self.message_user(request, f"Import completed. Orders created: {created_orders}.", level=messages.SUCCESS)
                    return redirect("admin:shopapp_order_changelist")
        else:
            form = OrderImportForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "form": form,
            "title": "Import orders from CSV",
            "subtitle": "Upload",
        }
        return render(request, "admin/csv_form.html", context)

    def _import_orders_from_csv(self, uploaded_file) -> int:
        try:
            decoded_file = uploaded_file.read().decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError("Cannot read file. Use UTF-8 CSV.") from error

        reader = csv.DictReader(StringIO(decoded_file))
        if not reader.fieldnames:
            raise ValueError("CSV is empty or contains no headers.")

        fieldnames = {field.strip() for field in reader.fieldnames if field}
        required_fields = {"delivery_address", "product_ids"}
        missing_fields = required_fields - fieldnames
        if missing_fields:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing_fields))}.")

        user_model = get_user_model()
        created_orders = 0

        with transaction.atomic():
            for row_index, row in enumerate(reader, start=2):
                row = {(key or "").strip(): value for key, value in row.items()}
                delivery_address = (row.get("delivery_address") or "").strip()
                if len(delivery_address) < 5:
                    raise ValueError(f"Row {row_index}: delivery address must be longer.")

                product_ids = self._parse_product_ids(row.get("product_ids", ""), row_index)
                products = list(Product.objects.filter(pk__in=product_ids, archived=False).order_by("pk"))
                if len(products) != len(set(product_ids)):
                    raise ValueError(f"Row {row_index}: one or more products were not found or archived.")

                user = None
                user_id_raw = (row.get("user_id") or "").strip()
                if user_id_raw:
                    try:
                        user = user_model.objects.get(pk=int(user_id_raw))
                    except (ValueError, user_model.DoesNotExist) as error:
                        raise ValueError(f"Row {row_index}: user id={user_id_raw} was not found.") from error

                order = Order.objects.create(
                    user=user,
                    delivery_address=delivery_address,
                    address=delivery_address,
                    city=(row.get("city") or "").strip(),
                    full_name=(row.get("full_name") or "").strip(),
                    email=(row.get("email") or "").strip(),
                    phone=(row.get("phone") or "").strip(),
                    promo_code=(row.get("promo_code") or "").strip(),
                    status=(row.get("status") or Order.STATUS_NEW).strip() or Order.STATUS_NEW,
                )
                for product in products:
                    order.products.add(product)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=1,
                        price_snapshot=product.final_price,
                    )
                created_orders += 1
        return created_orders

    def _parse_product_ids(self, raw_value, row_index: int):
        chunks = [chunk.strip() for chunk in (raw_value or "").split(",") if chunk.strip()]
        if not chunks:
            raise ValueError(f"Row {row_index}: product_ids must contain at least one id.")
        try:
            return [int(chunk) for chunk in chunks]
        except ValueError as error:
            raise ValueError(f"Row {row_index}: product_ids must contain only integers.") from error


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("pk", "product", "author", "rate", "created_at", "is_active")
    list_filter = ("is_active", "rate", "created_at")
    search_fields = ("author", "email", "text", "product__name")
    autocomplete_fields = ("product", "user")


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ("pk", "free_delivery_threshold", "delivery_cost", "express_delivery_cost")

    def has_add_permission(self, request):
        if ShopSettings.objects.exists():
            return False
        return super().has_add_permission(request)


admin.site.site_header = "Megano administration"
admin.site.site_title = "Megano admin"
admin.site.index_title = "Store management"
