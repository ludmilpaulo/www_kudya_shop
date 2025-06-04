import threading
from django.db import models
from django.utils import timezone
from customers.models import Customer
from drivers.models import Driver

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import random
import string


from .utils import generate_invoice
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Percentual de Desconto")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuário")
    order_count = models.IntegerField(default=0, verbose_name="Contagem de Pedidos")

    def __str__(self):
        return self.code


class Order(models.Model):
    DRIVER_COMMISSION_PERCENTAGE_DEFAULT = 5  # Example default percentage

    PROCESSING = 1
    READY = 2
    ONTHEWAY = 3
    DELIVERED = 4
    REJECTED = 5
    VERIFIED = 6

    STATUS_CHOICES = (
        (PROCESSING, "PROCESSANDO"),
        (READY, "Pedido Pronto"),
        (ONTHEWAY, "A caminho"),
        (DELIVERED, "Entregue"),
        (REJECTED, "Rejeitado"),
        (VERIFIED, "Verificado"),
    )

    PAID = "paid"
    UNPAID = "unpaid"

    PAYMENT_STATUS_CHOICES = (
        (PAID, "Paid"),
        (UNPAID, "Unpaid"),
    )

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, verbose_name="cliente"
    )
    store = models.ForeignKey(
        "stores.Store", on_delete=models.CASCADE, verbose_name="store"
    )
    driver = models.ForeignKey(
        Driver,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="motorista",
    )
    address = models.CharField(max_length=500, verbose_name="Endereco", blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_notes = models.TextField(blank=True, null=True, verbose_name="Notas de Entrega")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="Taxa de Entrega")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="Valor do Desconto")
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Cupom")
    use_current_location = models.BooleanField(default=False)
    location =  models.CharField(max_length=500, verbose_name="localizacao", blank=True, null=True)
    status = models.IntegerField(choices=STATUS_CHOICES, verbose_name="stado")
    payment_method = models.CharField(max_length=50, verbose_name="método de pagamento")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="criado em")
    picked_at = models.DateTimeField(blank=True, null=True, verbose_name="pegar em")
    invoice_pdf = models.FileField(
        upload_to="invoices/", null=True, blank=True, verbose_name="Fatura PDF"
    )
    secret_pin = models.CharField(
        max_length=6, verbose_name="PIN Secreto", blank=True, null=True
    )
    driver_commission_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=DRIVER_COMMISSION_PERCENTAGE_DEFAULT
    )
    proof_of_payment_store = models.FileField(
        upload_to="proof_of_payment/store/",
        null=True,
        blank=True,
        verbose_name="Prova de Pagamento ao Shop",
    )
    proof_of_payment_driver = models.FileField(
        upload_to="proof_of_payment/driver/",
        null=True,
        blank=True,
        verbose_name="Prova de Pagamento ao Motorista",
    )
    payment_status_store = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default=UNPAID,
        verbose_name="Status de Pagamento ao Store",
    )
    payment_status_driver = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default=UNPAID,
        verbose_name="Status de Pagamento ao Motorista",
    )
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    driver_commission = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
##########################################################################################
    def apply_coupon(self):
        print("Applying coupon...")
        if self.coupon and self.coupon.discount_percentage > 0:
            print(f"Coupon found: {self.coupon.code} with {self.coupon.discount_percentage}% discount")
            self.discount_amount = (self.total * self.coupon.discount_percentage) / 100
            print(f"Calculated discount amount: {self.discount_amount}")
            self.coupon.discount_percentage -= self.discount_amount / self.total * 100  # Deduct used points
            self.coupon.order_count += 1
            self.coupon.save()
            print(f"Coupon updated: {self.coupon.discount_percentage}% remaining, {self.coupon.order_count} order count")
        else:
            print("No valid coupon found or discount percentage is zero")
            self.discount_amount = 0.0

    def save(self, *args, **kwargs):
        print("Saving order...")
        self.apply_coupon()  # Apply the coupon before saving
        print(f"Total before discount: {self.total}")
        self.total -= self.discount_amount  # Apply discount
        print(f"Total after discount: {self.total}")
        self.total += self.delivery_fee  # Add delivery fee
        print(f"Total after adding delivery fee: {self.total}")
        super().save(*args, **kwargs)
        print("Order saved")

        if self.status == self.DELIVERED:
            print("Order delivered. Updating customer coupon...")
            customer_coupon, created = Coupon.objects.get_or_create(user=self.customer.user)
            if created:
                print("New coupon created for user")
                customer_coupon.code = f"{self.customer.user.username}_coupon"
                customer_coupon.save()
            else:
                print("Existing coupon found for user")

            print(f"Current discount percentage before update: {customer_coupon.discount_percentage}%")
            customer_coupon.discount_percentage = min(100, customer_coupon.discount_percentage + 1)  # Add 1% point for each delivered order
            customer_coupon.save()
            print(f"Updated discount percentage: {customer_coupon.discount_percentage}%")


########################################################################################
    @property
    def loyalty_discount(self):
        order_count = Order.objects.filter(customer=self.customer).count()
        discount = min(order_count, 10)  # Maximum discount is 10%
        return discount

    def calculate_driver_commission(self):
        if self.driver:
            total_commission = self.total * self.driver_commission_percentage / 100
            return total_commission
        return 0

    def save(self, *args, **kwargs):
        if not self.pk:
            self.driver_commission_percentage = (
                self.DRIVER_COMMISSION_PERCENTAGE_DEFAULT
            )
        if not self.secret_pin:
            self.secret_pin = "".join(random.choices(string.digits, k=6))
        if self.pk:
            old_status = Order.objects.get(pk=self.pk).status
            if old_status != self.status:
                logger.info(f"Order status changed from {old_status} to {self.status}")
                threading.Thread(target=self.send_status_update_email).start()
        super().save(*args, **kwargs)

    def send_status_update_email(self):
        logger.info(f"Sending status update email for order {self.id}")
        customer_email = self.customer.user.email
        store_email = self.store.user.email
        context = {
            "customer_name": self.customer.user.get_full_name(),
            "order_status": self.get_status_display(),
            "order_id": self.id,
            "order_total": self.total,
            "address": self.address,
            "order_details": self.order_details.all(),
            "secret_pin": self.secret_pin,
        }
        subject = "Atualização de Status do Pedido"
        message = render_to_string("email_templates/order_status_update.html", context)
        pdf_path, pdf_content = generate_invoice(self)
        self.invoice_pdf.save(
            f"order_{self.id}.pdf", ContentFile(pdf_content), save=False
        )
        self.save()

        email = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [customer_email, store_email],
        )
        email.attach(f"order_{self.id}.pdf", pdf_content, "application/pdf")
        email.content_subtype = "html"
        email.send()
        logger.info(f"Status update email sent for order {self.id}")


class OrderDetails(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="order_details",
        on_delete=models.CASCADE,
        verbose_name="Pedido",
    )
    product = models.ForeignKey(
        "stores.Product", on_delete=models.CASCADE, verbose_name="Refeição"
    )
    quantity = models.IntegerField(verbose_name="Quantidade")
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Detalhe do pedido"
        verbose_name_plural = "Detalhes dos pedidos"

    def __str__(self):
        return str(self.id)



