from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_profile_options"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="profile",
            constraint=models.UniqueConstraint(
                fields=("phone",),
                condition=~Q(phone=""),
                name="accounts_profile_unique_non_empty_phone",
            ),
        ),
    ]
