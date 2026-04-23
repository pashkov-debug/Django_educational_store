from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, redirect_to_login
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView

from .forms import (
    AvatarUpdateForm,
    BuyerAuthenticationForm,
    BuyerRegistrationForm,
    ProfileUpdateForm,
)
from .models import Profile


def can_edit_profile(current_user, profile_user) -> bool:
    return current_user.is_authenticated and (
        current_user.is_staff or current_user.pk == profile_user.pk
    )


class StoreLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    authentication_form = BuyerAuthenticationForm

    def get_success_url(self):
        return reverse("shopapp:index")

    def form_valid(self, form):
        messages.success(self.request, "Вы вошли в аккаунт.")
        return super().form_valid(form)


class StoreRegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = BuyerRegistrationForm
    success_url = reverse_lazy("shopapp:index")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Аккаунт создан, профиль пользователя подготовлен.")
        return HttpResponseRedirect(self.get_success_url())


class StoreLogoutView(LogoutView):
    next_page = reverse_lazy("shopapp:index")

    def post(self, request, *args, **kwargs):
        messages.success(request, "Вы вышли из аккаунта.")
        return super().post(request, *args, **kwargs)


class AccountDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "shopapp/storefront/account.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        latest_orders = (
            self.request.user.orders.prefetch_related("products")
            .order_by("-created_at")[:5]
        )
        context.update(
            {
                "profile": profile,
                "latest_orders": latest_orders,
            }
        )
        return context


class AboutMeView(FormView):
    template_name = "shopapp/storefront/about_me.html"
    form_class = AvatarUpdateForm
    success_url = reverse_lazy("accounts:about_me")

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() == "post" and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user if self.request.user.is_authenticated else None
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Аватар успешно обновлён.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_object = None
        if self.request.user.is_authenticated:
            profile_object, _ = Profile.objects.get_or_create(user=self.request.user)
        context.update(
            {
                "profile_object": profile_object,
            }
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "shopapp/storefront/profile.html"
    form_class = ProfileUpdateForm
    raise_exception = True

    def get_target_user(self):
        user_pk = self.kwargs.get("user_pk")
        if user_pk is None:
            return self.request.user
        return get_object_or_404(get_user_model(), pk=user_pk)

    def dispatch(self, request, *args, **kwargs):
        self.target_user = self.get_target_user()
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return can_edit_profile(self.request.user, self.target_user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.target_user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            f"Профиль пользователя {self.target_user.username} успешно обновлён.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        if self.target_user.pk == self.request.user.pk and "user_pk" not in self.kwargs:
            return reverse("accounts:profile")
        return reverse("accounts:user_detail", kwargs={"pk": self.target_user.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_object, _ = Profile.objects.get_or_create(user=self.target_user)
        context.update(
            {
                "target_user": self.target_user,
                "profile_object": profile_object,
                "can_edit_profile": can_edit_profile(self.request.user, self.target_user),
                "back_url": (
                    reverse("accounts:account")
                    if self.target_user.pk == self.request.user.pk
                    else reverse("accounts:user_detail", kwargs={"pk": self.target_user.pk})
                ),
            }
        )
        return context


class UserListView(ListView):
    model = get_user_model()
    template_name = "shopapp/storefront/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return get_user_model().objects.order_by("username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_cards = []
        for listed_user in context["users"]:
            profile, _ = Profile.objects.get_or_create(user=listed_user)
            user_cards.append(
                {
                    "user": listed_user,
                    "profile": profile,
                    "can_edit_profile": can_edit_profile(self.request.user, listed_user),
                }
            )
        context["user_cards"] = user_cards
        return context


class UserDetailView(DetailView):
    model = get_user_model()
    template_name = "shopapp/storefront/user_detail.html"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.object)
        context.update(
            {
                "profile": profile,
                "can_edit_profile": can_edit_profile(self.request.user, self.object),
            }
        )
        return context
