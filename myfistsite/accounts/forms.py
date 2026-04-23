from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile


class BuyerAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Введите логин",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Введите пароль",
                "autocomplete": "current-password",
            }
        ),
    )


class BuyerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Введите email",
                "autocomplete": "email",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "Логин",
        }
        help_texts = {
            "username": "",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "placeholder": "Придумайте логин",
                "autocomplete": "username",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": "Придумайте пароль",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": "Повторите пароль",
                "autocomplete": "new-password",
            }
        )
        self.fields["password1"].label = "Пароль"
        self.fields["password2"].label = "Подтверждение пароля"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email


class AvatarUpdateForm(forms.Form):
    avatar = forms.ImageField(
        label="Аватар",
        required=False,
        widget=forms.ClearableFileInput(),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.profile = None
        if user is not None and getattr(user, "is_authenticated", False):
            self.profile, _ = Profile.objects.get_or_create(user=user)

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and avatar.size > settings.MAX_UPLOAD_SIZE:
            raise forms.ValidationError("Размер аватарки должен быть не больше 2 МБ.")
        return avatar

    def save(self):
        if not self.profile:
            raise ValueError("Нельзя сохранить аватар для неавторизованного пользователя.")

        avatar = self.cleaned_data.get("avatar")
        if avatar:
            self.profile.avatar = avatar
            self.profile.save(update_fields=["avatar", "updated_at"])
        return self.profile


class ProfileUpdateForm(forms.Form):
    full_name = forms.CharField(
        label="Ф. И. О.",
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Введите Ф. И. О.",
                "autocomplete": "name",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Введите email",
                "autocomplete": "email",
            }
        ),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=32,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Введите телефон",
                "autocomplete": "tel",
            }
        ),
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.profile, _ = Profile.objects.get_or_create(user=user)
        if not self.is_bound:
            self.initial["full_name"] = self.profile.full_name
            self.initial["email"] = user.email
            self.initial["phone"] = self.profile.phone

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()
        if user_model.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_full_name(self):
        value = self.cleaned_data["full_name"].strip()
        if not value:
            raise forms.ValidationError("Укажите Ф. И. О.")
        return value

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if phone and Profile.objects.exclude(pk=self.profile.pk).filter(phone=phone).exists():
            raise forms.ValidationError("Пользователь с таким телефоном уже существует.")
        return phone

    def save(self):
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["email"])

        self.profile.full_name = self.cleaned_data["full_name"]
        self.profile.phone = self.cleaned_data["phone"]
        self.profile.save(update_fields=["full_name", "phone", "updated_at"])
        return self.profile
