from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0007_product_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="promo_code",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
