# Generated by Django 5.0.3 on 2024-07-12 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0005_alter_order_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="address",
            field=models.CharField(
                blank=True, max_length=500, null=True, verbose_name="Endereco"
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.IntegerField(
                choices=[
                    (1, "Cozinhando"),
                    (2, "Pedido Pronto"),
                    (3, "A caminho"),
                    (4, "Entregue"),
                    (5, "Rejeitado"),
                    (6, "Verificado"),
                ],
                verbose_name="stado",
            ),
        ),
    ]