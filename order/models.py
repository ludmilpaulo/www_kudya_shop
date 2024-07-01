import threading
from django.db import models
from django.utils import timezone
from curtomers.models import Customer
from drivers.models import Driver
from info.models import Chat
from restaurants.models import Meal, Restaurant
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import random
import string
from .utils import generate_invoice
from django.conf import settings
import logging


logger = logging.getLogger(__name__)

class Order(models.Model):
    COOKING = 1
    READY = 2
    ONTHEWAY = 3
    DELIVERED = 4


    STATUS_CHOICES = (
        (COOKING, "Cozinhando"),
        (READY, "Pedido Pronto"),
        (ONTHEWAY, "A caminho"),
        (DELIVERED, "Entregue"),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='cliente')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name='restaurante')
    driver = models.ForeignKey(Driver, blank=True, null=True, on_delete=models.CASCADE, verbose_name='motorista')
    address = models.CharField(max_length=500, verbose_name='Endereco')
    total = models.IntegerField()
    status = models.IntegerField(choices=STATUS_CHOICES, verbose_name='stado')
    payment_method = models.CharField(max_length=50, verbose_name='método de pagamento')
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE, null=True, blank=True, related_name='order_chat')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='criado em')
    picked_at = models.DateTimeField(blank=True, null=True, verbose_name='pegar em')
    invoice_pdf = models.FileField(upload_to='invoices/', null=True, blank=True, verbose_name='Fatura PDF')
    secret_pin = models.CharField(max_length=6, verbose_name='PIN Secreto', blank=True, null=True)
    driver_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=1)


    def calculate_driver_commission(self):
        if self.driver:
            total_commission = (self.total * self.driver_commission_percentage / 100)
            return total_commission
        return 0

    def save(self, *args, **kwargs):
        if not self.pk:
            self.driver_commission_percentage = self.DRIVER_COMMISSION_PERCENTAGE_DEFAULT
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.secret_pin:
            self.secret_pin = ''.join(random.choices(string.digits, k=6))
        if self.pk:
            old_status = Order.objects.get(pk=self.pk).status
            if old_status != self.status:
                logger.info(f"Order status changed from {old_status} to {self.status}")
                threading.Thread(target=self.send_status_update_email).start()
        super().save(*args, **kwargs)

    def send_status_update_email(self):
        logger.info(f"Sending status update email for order {self.id}")
        customer_email = self.customer.user.email
        restaurant_email = self.restaurant.user.email
        context = {
            'customer_name': self.customer.user.get_full_name(),
            'order_status': self.get_status_display(),
            'order_id': self.id,
            'order_total': self.total,
            'address': self.address,
            'order_details': self.order_details.all(),
            'secret_pin': self.secret_pin,
        }
        subject = 'Atualização de Status do Pedido'
        message = render_to_string('email_templates/order_status_update.html', context)
        pdf_path, pdf_content = generate_invoice(self)
        self.invoice_pdf.save(f"order_{self.id}.pdf", ContentFile(pdf_content), save=False)
        self.save()

        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [customer_email, restaurant_email])
        email.attach(f"order_{self.id}.pdf", pdf_content, 'application/pdf')
        email.content_subtype = "html"
        email.send()
        logger.info(f"Status update email sent for order {self.id}")



class OrderDetails(models.Model):
    order = models.ForeignKey(Order, related_name='order_details', on_delete=models.CASCADE, verbose_name='Pedido')
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, verbose_name='Refeição')
    quantity = models.IntegerField(verbose_name='Quantidade')
    sub_total = models.IntegerField()

    class Meta:
        verbose_name ='Detalhe do pedido'
        verbose_name_plural ='Detalhes dos pedidos'

    def __str__(self):
        return str(self.id)
