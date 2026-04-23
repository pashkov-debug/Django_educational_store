from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin


from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "full_name", "phone", "avatar", "created_at")
    list_display_links = ("pk", "user")
    search_fields = ("user__username", "user__email", "full_name", "phone")


User = get_user_model()
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class StoreUserAdmin(UserAdmin):
    def delete_model(self, request, obj):
        obj.is_active = False
        obj.save(update_fields=["is_active"])

    def delete_queryset(self, request, queryset):
        queryset.update(is_active=False)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
