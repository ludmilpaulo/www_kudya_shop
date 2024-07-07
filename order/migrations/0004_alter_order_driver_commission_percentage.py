# Generated by Django 5.0.3 on 2024-07-07 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_alter_order_options_order_driver_commission_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='driver_commission_percentage',
            field=models.DecimalField(decimal_places=2, default=5, max_digits=5),
        ),
    ]
