
from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy
from django.views.generic import RedirectView

app_name = "accounts"

urlpatterns = [
    path("login/", RedirectView.as_view(pattern_name="shopapp:sign_in", permanent=False), name="login"),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy("shopapp:index")), name="logout"),
    path("register/", RedirectView.as_view(pattern_name="shopapp:sign_up", permanent=False), name="register"),
    path("account/", RedirectView.as_view(pattern_name="shopapp:account", permanent=False), name="account"),
    path("about-me/", RedirectView.as_view(pattern_name="shopapp:profile", permanent=False), name="about_me"),
    path("profile/", RedirectView.as_view(pattern_name="shopapp:profile", permanent=False), name="profile"),
    path("users/", RedirectView.as_view(url="/admin/auth/user/", permanent=False), name="users_list"),
    path("users/<int:pk>/", RedirectView.as_view(url="/admin/auth/user/", permanent=False), name="user_detail"),
    path("users/<int:user_pk>/edit/", RedirectView.as_view(pattern_name="shopapp:profile", permanent=False), name="user_profile_update"),
]
