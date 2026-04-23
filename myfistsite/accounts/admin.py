from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "full_name", "phone", "avatar", "created_at")
    list_display_links = ("pk", "user")
    search_fields = ("user__username", "user__email", "full_name", "phone")
