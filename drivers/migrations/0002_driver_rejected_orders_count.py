# Generated by Django 5.0.3 on 2024-07-11 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drivers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="driver",
            name="rejected_orders_count",
            field=models.IntegerField(default=0, verbose_name="Pedidos Rejeitados"),
        ),
    ]