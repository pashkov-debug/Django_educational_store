from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_profile_avatar"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="profile",
            options={
                "ordering": ("user__username",),
                "permissions": (
                    ("view_api_docs", "Может просматривать API-документацию"),
                ),
                "verbose_name": "Профиль",
                "verbose_name_plural": "Профили",
            },
        ),
    ]