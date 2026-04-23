from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Q


def profile_avatar_upload_to(instance, filename: str) -> str:
    file_name = Path(filename).name
    return f"users/user_{instance.user_id}/avatars/{file_name}"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    full_name = models.CharField("Ф. И. О.", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    avatar = models.ImageField(
        "Аватар",
        upload_to=profile_avatar_upload_to,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"
        ordering = ("user__username",)
        permissions = (
            ("view_api_docs", "Может просматривать API-документацию"),
        )
        constraints = [
            models.UniqueConstraint(
                fields=["phone"],
                condition=~Q(phone=""),
                name="accounts_profile_unique_non_empty_phone",
            ),
        ]

    def __str__(self) -> str:
        return f"Профиль {self.user.username}"
