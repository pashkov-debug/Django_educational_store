from django.urls import path

from .views import (
    AboutMeView,
    AccountDashboardView,
    ProfileUpdateView,
    StoreLoginView,
    StoreLogoutView,
    StoreRegisterView,
    UserDetailView,
    UserListView,
)

app_name = "accounts"

urlpatterns = [
    path("login/", StoreLoginView.as_view(), name="login"),
    path("logout/", StoreLogoutView.as_view(), name="logout"),
    path("register/", StoreRegisterView.as_view(), name="register"),
    path("account/", AccountDashboardView.as_view(), name="account"),
    path("about-me/", AboutMeView.as_view(), name="about_me"),
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
    path("users/", UserListView.as_view(), name="users_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("users/<int:user_pk>/edit/", ProfileUpdateView.as_view(), name="user_profile_update"),
]
