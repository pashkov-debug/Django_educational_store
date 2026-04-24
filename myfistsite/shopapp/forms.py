from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Category, Manufacturer, Order, Product


class ProductCatalogFilterForm(forms.Form):
    q = forms.CharField(
        label="Название",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Название товара"}),
    )
    category = forms.CharField(label="Категория", required=False)
    manufacturer = forms.ModelChoiceField(
        label="Производитель",
        required=False,
        queryset=Manufacturer.objects.none(),
        empty_label="Любой производитель",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    price_min = forms.DecimalField(
        label="Цена от",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-input", "placeholder": "от", "step": "0.01", "min": "0"}),
    )
    price_max = forms.DecimalField(
        label="Цена до",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-input", "placeholder": "до", "step": "0.01", "min": "0"}),
    )
    sort = forms.ChoiceField(
        label="Сортировка",
        required=False,
        choices=(
            ("name", "по названию"),
            ("popular", "по популярности"),
            ("price", "по цене"),
            ("new", "по новизне"),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    direction = forms.ChoiceField(
        label="Направление",
        required=False,
        choices=(
            ("asc", "по возрастанию"),
            ("desc", "по убыванию"),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manufacturer"].queryset = Manufacturer.objects.filter(archived=False).order_by("name")

    def clean_category(self):
        value = (self.cleaned_data.get("category") or "").strip()
        if not value:
            return ""

        query = Q(slug=value)
        if value.isdigit():
            query |= Q(pk=int(value))

        exists = Category.objects.filter(query, archived=False, is_active=True).exists()
        if not exists:
            raise forms.ValidationError("Выбранная категория не найдена.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        price_min = cleaned_data.get("price_min")
        price_max = cleaned_data.get("price_max")

        if price_min is not None and price_max is not None and price_min > price_max:
            self.add_error("price_max", "Цена до должна быть больше или равна цене от.")

        return cleaned_data


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name",
            "short_description",
            "description",
            "image",
            "category",
            "manufacturer",
            "price",
            "discount",
            "sort_index",
            "is_featured",
            "is_limited_edition",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Например, Игровая мышь"}),
            "short_description": forms.TextInput(attrs={"class": "form-input", "placeholder": "Короткое описание для каталога"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 5, "placeholder": "Полное описание товара"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "manufacturer": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-input", "step": "0.01", "min": "0"}),
            "discount": forms.NumberInput(attrs={"class": "form-input", "min": "0", "max": "100"}),
            "sort_index": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
        }
        labels = {
            "name": "Название",
            "short_description": "Краткое описание",
            "description": "Описание",
            "image": "Изображение товара",
            "category": "Категория",
            "manufacturer": "Производитель",
            "price": "Цена",
            "discount": "Скидка, %",
            "sort_index": "Индекс сортировки",
            "is_featured": "Топ-товар",
            "is_limited_edition": "Ограниченный тираж",
        }
        help_texts = {
            "image": "Необязательно. Можно заменить или очистить позже.",
            "sort_index": "Чем меньше число, тем выше товар в блоках главной страницы.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["short_description"].required = False
        self.fields["image"].required = False
        self.fields["category"].required = False
        self.fields["manufacturer"].required = False
        self.fields["discount"].required = False
        self.fields["sort_index"].required = False
        self.fields["is_featured"].required = False
        self.fields["is_limited_edition"].required = False

        self.fields["discount"].initial = 0
        self.fields["sort_index"].initial = 100

        category_queryset = Category.objects.filter(archived=False, is_active=True)
        manufacturer_queryset = Manufacturer.objects.filter(archived=False)

        if self.instance.pk:
            if self.instance.category_id:
                category_queryset = Category.objects.filter(Q(archived=False, is_active=True) | Q(pk=self.instance.category_id))
            if self.instance.manufacturer_id:
                manufacturer_queryset = Manufacturer.objects.filter(Q(archived=False) | Q(pk=self.instance.manufacturer_id))

        self.fields["category"].queryset = category_queryset.order_by("sort_index", "name").distinct()
        self.fields["manufacturer"].queryset = manufacturer_queryset.order_by("name").distinct()
        self.fields["category"].empty_label = "Без категории"
        self.fields["manufacturer"].empty_label = "Без производителя"

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Цена должна быть больше нуля.")
        return price

    def clean_discount(self):
        discount = self.cleaned_data.get("discount")
        if discount is None:
            return 0
        if discount < 0 or discount > 100:
            raise forms.ValidationError("Скидка должна быть в диапазоне от 0 до 100.")
        return discount

    def clean_sort_index(self):
        sort_index = self.cleaned_data.get("sort_index")
        if sort_index is None:
            return 100
        return sort_index


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("delivery_address", "promo_code", "status", "user", "products")
        widgets = {
            "delivery_address": forms.Textarea(attrs={"class": "form-textarea", "rows": 4, "placeholder": "Введите адрес доставки"}),
            "promo_code": forms.TextInput(attrs={"class": "form-input", "placeholder": "Например, SALE10"}),
            "status": forms.TextInput(attrs={"class": "form-input"}),
            "user": forms.Select(attrs={"class": "form-select"}),
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
            product_queryset = Product.objects.filter(Q(archived=False) | Q(pk__in=self.instance.products.values_list("pk", flat=True)))
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
        widget=forms.ClearableFileInput(attrs={"class": "form-input"}),
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not csv_file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Загрузите файл с расширением .csv.")
        return csv_file


class CheckoutCustomerForm(forms.Form):
    full_name = forms.CharField(
        label="Ф. И. О.",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Иван Иванов"}),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "user@example.com"}),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "+7 900 000 00 00"}),
    )
    password = forms.CharField(
        label="Пароль для регистрации",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Необязательно"}),
        help_text="Для гостя необязательно. Если заполнить — будет создан аккаунт.",
    )
    password_confirm = forms.CharField(
        label="Повторите пароль",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Повторите пароль"}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.profile = None
        if self.user and self.user.is_authenticated:
            self.profile = getattr(self.user, "profile", None)

    def clean_full_name(self):
        value = (self.cleaned_data.get("full_name") or "").strip()

        if value:
            return value

        if self.profile and self.profile.full_name:
            return self.profile.full_name.strip()

        if self.user and self.user.is_authenticated:
            full_name = " ".join(
                part for part in [self.user.first_name, self.user.last_name] if part
            ).strip()
            if full_name:
                return full_name
            return self.user.username

        raise forms.ValidationError("Обязательное поле.")

    def clean_email(self):
        value = (self.cleaned_data.get("email") or "").strip().lower()

        if value:
            return value

        if self.user and self.user.is_authenticated and self.user.email:
            return self.user.email.strip().lower()

        raise forms.ValidationError("Обязательное поле.")

    def clean_phone(self):
        value = (self.cleaned_data.get("phone") or "").strip()

        if not value and self.profile and self.profile.phone:
            value = self.profile.phone.strip()

        if not value:
            raise forms.ValidationError("Обязательное поле.")

        digits = "".join(symbol for symbol in value if symbol.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError("Укажите корректный телефон. Минимум 10 цифр.")

        return value

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password") or ""
        password_confirm = cleaned_data.get("password_confirm") or ""
        email = cleaned_data.get("email")

        if self.user and self.user.is_authenticated:
            return cleaned_data

        if password or password_confirm:
            if password != password_confirm:
                self.add_error("password_confirm", "Пароли не совпадают.")
            if len(password) < 6:
                self.add_error("password", "Пароль должен быть не короче 6 символов.")

            user_model = get_user_model()
            if email and user_model.objects.filter(email=email).exists():
                self.add_error("email", "Пользователь с указанным email существует, вы можете авторизоваться.")

        return cleaned_data


class CheckoutDeliveryForm(forms.Form):
    delivery_type = forms.ChoiceField(
        label="Способ доставки",
        choices=Order.DeliveryType.choices,
        widget=forms.RadioSelect,
    )
    city = forms.CharField(
        label="Город",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Москва"}),
    )
    address = forms.CharField(
        label="Адрес",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ул. Тестовая, дом 1"}),
    )

    def __init__(self, *args, **kwargs):
        self.cart_total = kwargs.pop("cart_total")
        self.shop_settings = kwargs.pop("shop_settings")
        super().__init__(*args, **kwargs)

    def clean_address(self):
        address = self.cleaned_data["address"].strip()
        if len(address) < 5:
            raise forms.ValidationError("Укажите более полный адрес.")
        return address


class CheckoutPaymentForm(forms.Form):
    payment_type = forms.ChoiceField(
        label="Способ оплаты",
        choices=Order.PaymentType.choices,
        widget=forms.RadioSelect,
    )


class CheckoutConfirmForm(forms.Form):
    comment = forms.CharField(
        label="Комментарий к заказу",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 4, "placeholder": "Комментарий для магазина"}),
    )