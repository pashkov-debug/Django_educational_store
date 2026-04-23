from django import forms
from django.db.models import Q

from .models import Order, Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "description", "image", "price", "discount")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Например, Игровая мышь"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Краткое описание товара"}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "discount": forms.NumberInput(attrs={"min": "0", "max": "100"}),
        }
        labels = {
            "name": "Название",
            "description": "Описание",
            "image": "Изображение товара",
            "price": "Цена",
            "discount": "Скидка, %",
        }
        help_texts = {
            "image": "Необязательно. Можно заменить или очистить позже.",
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Цена должна быть больше нуля.")
        return price

    def clean_discount(self):
        discount = self.cleaned_data["discount"]
        if discount < 0 or discount > 100:
            raise forms.ValidationError("Скидка должна быть в диапазоне от 0 до 100.")
        return discount


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("delivery_address", "promo_code", "status", "user", "products")
        widgets = {
            "delivery_address": forms.Textarea(attrs={"rows": 4, "placeholder": "Введите адрес доставки"}),
            "promo_code": forms.TextInput(attrs={"placeholder": "Например, SALE10"}),
            "products": forms.CheckboxSelectMultiple(),
        }
        labels = {
            "delivery_address": "Адрес доставки",
            "promo_code": "Промокод",
            "status": "Статус",
            "user": "Пользователь",
            "products": "Товары",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].required = False

        product_queryset = Product.objects.filter(archived=False)
        if self.instance.pk:
            product_queryset = Product.objects.filter(
                Q(archived=False) | Q(pk__in=self.instance.products.values_list("pk", flat=True))
            )
        self.fields["products"].queryset = product_queryset.order_by("name").distinct()

    def clean_delivery_address(self):
        delivery_address = self.cleaned_data["delivery_address"].strip()
        if len(delivery_address) < 10:
            raise forms.ValidationError("Укажите более полный адрес доставки.")
        return delivery_address

    def clean_products(self):
        products = self.cleaned_data["products"]
        if not products:
            raise forms.ValidationError("Выберите хотя бы один товар.")
        return products


class OrderImportForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV-файл с заказами",
        help_text="Поддерживается только CSV в кодировке UTF-8.",
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not csv_file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Загрузите файл с расширением .csv.")
        return csv_file
