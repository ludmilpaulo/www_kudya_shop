# Generated by Django 5.0.3 on 2024-07-21 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("report", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Coupon",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.CharField(max_length=50, unique=True, verbose_name="Código"),
                ),
                (
                    "discount_percentage",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        verbose_name="Percentual de Desconto",
                    ),
                ),
                ("valid_from", models.DateTimeField(verbose_name="Válido de")),
                ("valid_to", models.DateTimeField(verbose_name="Válido até")),
                ("active", models.BooleanField(default=True, verbose_name="Ativo")),
            ],
        ),
    ]
