from django.db import models

from order.models import Order
from restaurants.models import Restaurant


# Create your models here.


class Invoice(models.Model):
    PAID = 'paid'
    UNPAID = 'unpaid'

    STATUS_CHOICES = (
        (PAID, 'Pago'),
        (UNPAID, 'Não Pago'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='pedido')
    status = models.IntegerField(choices=STATUS_CHOICES, default=UNPAID, verbose_name='estado')
    shop = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name='loja')

    def __str__(self):
        return f"Invoice for Order {self.order.id}"