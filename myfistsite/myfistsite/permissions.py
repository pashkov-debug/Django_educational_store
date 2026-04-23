from rest_framework.permissions import BasePermission


class CanViewApiDocs(BasePermission):
    message = "У вас нет прав на просмотр API-документации."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (user.is_staff or user.is_superuser or user.has_perm("accounts.view_api_docs"))
        )