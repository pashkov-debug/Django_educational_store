import csv
from io import StringIO

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import OrderImportForm
from .models import Category, Manufacturer, Order, Product


class SoftDeleteAdminMixin:
    archive_field_name = "archived"

    def delete_model(self, request, obj):
        setattr(obj, self.archive_field_name, True)
        obj.save(update_fields=[self.archive_field_name])

    def delete_queryset(self, request, queryset):
        queryset.update(**{self.archive_field_name: True})

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


@admin.action(description="Архивировать выбранные категории")
def archive_categories(modeladmin, request, queryset):
    queryset.update(archived=True, is_active=False)


@admin.action(description="Восстановить выбранные категории")
def restore_categories(modeladmin, request, queryset):
    queryset.update(archived=False, is_active=True)


@admin.action(description="Архивировать выбранных производителей")
def archive_manufacturers(modeladmin, request, queryset):
    queryset.update(archived=True)


@admin.action(description="Восстановить выбранных производителей")
def restore_manufacturers(modeladmin, request, queryset):
    queryset.update(archived=False)


@admin.action(description="Архивировать выбранные товары")
def archive_products(modeladmin, request, queryset):
    queryset.update(archived=True)


@admin.action(description="Восстановить выбранные товары из архива")
def restore_products(modeladmin, request, queryset):
    queryset.update(archived=False)


@admin.action(description="Архивировать выбранные заказы")
def archive_orders(modeladmin, request, queryset):
    queryset.update(archived=True)


@admin.action(description="Восстановить выбранные заказы из архива")
def restore_orders(modeladmin, request, queryset):
    queryset.update(archived=False)


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("pk", "name", "parent", "is_active", "is_featured", "sort_index", "archived")
    list_display_links = ("pk", "name")
    search_fields = ("name", "slug")
    list_filter = ("archived", "is_active", "is_featured", "parent")
    prepopulated_fields = {"slug": ("name",)}
    actions = (archive_categories, restore_categories)

    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "icon")}),
        ("Отображение", {"fields": ("is_active", "is_featured", "sort_index", "archived")}),
    )


@admin.register(Manufacturer)
class ManufacturerAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("pk", "name", "slug", "archived")
    list_display_links = ("pk", "name")
    search_fields = ("name", "slug", "description")
    list_filter = ("archived",)
    prepopulated_fields = {"slug": ("name",)}
    actions = (archive_manufacturers, restore_manufacturers)


class ProductOrderInline(admin.TabularInline):
    model = Order.products.through
    fk_name = "product"
    extra = 0
    can_delete = False
    verbose_name = "Заказ"
    verbose_name_plural = "Заказы с этим товаром"
    fields = ("order_link", "created_at", "status", "user")
    readonly_fields = ("order_link", "created_at", "status", "user")

    @admin.display(description="Заказ")
    def order_link(self, obj):
        url = reverse("admin:shopapp_order_change", args=(obj.order_id,))
        return format_html('<a href="{}">Заказ #{}</a>', url, obj.order_id)

    @admin.display(description="Создан")
    def created_at(self, obj):
        return obj.order.created_at

    @admin.display(description="Статус")
    def status(self, obj):
        return obj.order.status

    @admin.display(description="Пользователь")
    def user(self, obj):
        return obj.order.user

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "category",
        "manufacturer",
        "image_preview",
        "price",
        "discount",
        "final_price_display",
        "sort_index",
        "is_featured",
        "is_limited_edition",
        "archived",
    )
    list_display_links = ("pk", "name")
    search_fields = ("name", "short_description", "description", "category__name", "manufacturer__name")
    list_filter = ("archived", "is_featured", "is_limited_edition", "category", "manufacturer", "created_at")
    actions = (archive_products, restore_products)
    inlines = (ProductOrderInline,)
    readonly_fields = ("image_preview",)
    autocomplete_fields = ("category", "manufacturer", "created_by")

    fieldsets = (
        (None, {"fields": ("name", "short_description", "description", "image", "image_preview", "archived")}),
        ("Каталог", {"fields": ("category", "manufacturer", "sort_index", "is_featured", "is_limited_edition")}),
        ("Цена", {"fields": ("price", "discount")}),
        ("Служебные данные", {"fields": ("created_by",)}),
    )

    @admin.display(description="Превью")
    def image_preview(self, obj):
        if not obj.image:
            return "Нет изображения"
        return format_html(
            '<img src="{}" alt="{}" style="max-height: 80px; border-radius: 8px;" />',
            obj.image.url,
            obj.name,
        )

    @admin.display(description="Цена со скидкой")
    def final_price_display(self, obj):
        return obj.final_price


@admin.register(Order)
class OrderAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    change_list_template = "shopapp/orders_changelist.html"
    list_display = ("pk", "delivery_address_short", "status", "user", "created_at", "products_count", "total_price_display", "archived")
    list_display_links = ("pk",)
    search_fields = ("delivery_address", "status", "user__username")
    list_filter = ("archived", "status", "created_at")
    actions = (archive_orders, restore_orders)

    @admin.display(description="Адрес")
    def delivery_address_short(self, obj):
        max_length = 48
        if len(obj.delivery_address) <= max_length:
            return obj.delivery_address
        return f"{obj.delivery_address[:max_length]}..."

    @admin.display(description="Кол-во товаров")
    def products_count(self, obj):
        return obj.products.count()

    @admin.display(description="Сумма")
    def total_price_display(self, obj):
        return obj.total_price

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
                    self.message_user(
                        request,
                        f"Импорт завершён. Создано заказов: {created_orders}.",
                        level=messages.SUCCESS,
                    )
                    return redirect("admin:shopapp_order_changelist")
        else:
            form = OrderImportForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "form": form,
            "title": "Импорт заказов из CSV",
            "subtitle": "Загрузка файла",
        }
        return render(request, "admin/csv_form.html", context)

    def _import_orders_from_csv(self, uploaded_file) -> int:
        try:
            decoded_file = uploaded_file.read().decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError("Не удалось прочитать файл. Используйте CSV в кодировке UTF-8.") from error

        reader = csv.DictReader(StringIO(decoded_file))
        if not reader.fieldnames:
            raise ValueError("CSV-файл пустой или не содержит заголовков.")

        fieldnames = {field.strip() for field in reader.fieldnames if field}
        required_fields = {"delivery_address", "product_ids"}
        missing_fields = required_fields - fieldnames
        if missing_fields:
            missing_fields_display = ", ".join(sorted(missing_fields))
            raise ValueError(f"В CSV отсутствуют обязательные колонки: {missing_fields_display}.")

        user_model = get_user_model()
        created_orders = 0

        with transaction.atomic():
            for row_index, row in enumerate(reader, start=2):
                row = {(key or "").strip(): value for key, value in row.items()}
                delivery_address = (row.get("delivery_address") or "").strip()
                if len(delivery_address) < 10:
                    raise ValueError(f"Строка {row_index}: адрес доставки должен быть не короче 10 символов.")

                product_ids = self._parse_product_ids(row.get("product_ids", ""), row_index)
                products = list(Product.objects.filter(pk__in=product_ids, archived=False).order_by("pk"))
                if len(products) != len(set(product_ids)):
                    raise ValueError(f"Строка {row_index}: один или несколько товаров не найдены или находятся в архиве.")

                user = None
                user_id_raw = (row.get("user_id") or "").strip()
                if user_id_raw:
                    try:
                        user = user_model.objects.get(pk=int(user_id_raw))
                    except (ValueError, user_model.DoesNotExist) as error:
                        raise ValueError(f"Строка {row_index}: пользователь с id={user_id_raw} не найден.") from error

                order = Order.objects.create(
                    delivery_address=delivery_address,
                    promo_code=(row.get("promo_code") or "").strip(),
                    status=(row.get("status") or Order._meta.get_field("status").default).strip() or Order._meta.get_field("status").default,
                    user=user,
                )
                order.products.set(products)
                created_orders += 1

        return created_orders

    def _parse_product_ids(self, raw_value: str, row_index: int) -> list[int]:
        normalized_value = raw_value.replace("|", ",")
        parts = [part.strip() for part in normalized_value.split(",") if part.strip()]
        if not parts:
            raise ValueError(f"Строка {row_index}: укажите хотя бы один product_id.")

        try:
            return [int(part) for part in parts]
        except ValueError as error:
            raise ValueError(f"Строка {row_index}: product_ids должны содержать только числовые идентификаторы.") from error