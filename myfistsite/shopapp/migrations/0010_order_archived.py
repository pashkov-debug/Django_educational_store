from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0009_product_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="archived",
            field=models.BooleanField(default=False),
        ),
    ]
