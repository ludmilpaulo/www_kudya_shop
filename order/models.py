from django.db import models
from django.utils import timezone
from curtomers.models import Customer
from drivers.models import Driver
from info.models import Chat
from restaurants.models import Meal, Restaurant
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from www_kudya_shop import settings
from .utils import generate_pdf
import os
import random
import string

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
    secret_pin = models.CharField(max_length=6, verbose_name='PIN Secreto', blank=True, null=True)  # New field

    class Meta:
        verbose_name ='Pedido'
        verbose_name_plural ='Pedidos'

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.secret_pin:
            self.secret_pin = ''.join(random.choices(string.digits, k=6))  # Generate a 6-digit PIN
        if self.pk:
            old_status = Order.objects.get(pk=self.pk).status
            if old_status != self.status:
                self.send_status_update_email()
        super().save(*args, **kwargs)

    def send_status_update_email(self):
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
        pdf = generate_pdf('email_templates/order_invoice.html', context)
        pdf_path = os.path.join('invoices', f'order_{self.id}.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(pdf.read())
        self.invoice_pdf = pdf_path
        self.save()

        email = EmailMessage(subject, '', settings.DEFAULT_FROM_EMAIL, [customer_email, restaurant_email])
        email.attach('invoice.pdf', open(pdf_path, 'rb').read(), 'application/pdf')
        email.send()

def send_order_email(email, order, is_restaurant=False):
    context = {
        'customer_name': order.customer.user.get_full_name(),
        'order_status': order.get_status_display(),
        'order_id': order.id,
        'order_total': order.total,
        'address': order.address,
        'order_details': order.order_details.all(),
        'secret_pin': order.secret_pin,
    }
    subject = 'Nova Pedido' if is_restaurant else 'Pedido Recebido'
    message = render_to_string('email_templates/order_confirmation.html', context)
    pdf = generate_pdf('email_templates/order_invoice.html', context)
    pdf_path = os.path.join('invoices', f'order_{order.id}.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf.read())
    order.invoice_pdf = pdf_path
    order.save()

    email = EmailMessage(subject, '', 'your-email@gmail.com', [email])
    email.attach('invoice.pdf', open(pdf_path, 'rb').read(), 'application/pdf')
    email.send()




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



