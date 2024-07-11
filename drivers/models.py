from email.message import EmailMessage
from venv import logger
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# In your models.py
class Driver(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="driver", verbose_name="Utilizador"
    )
    avatar = models.ImageField(upload_to="driver/", blank=True)
    phone = models.CharField(max_length=500, blank=True, verbose_name="telefone")
    address = models.CharField(max_length=500, blank=True, verbose_name="Endereço")
    location = models.CharField(max_length=500, blank=True, verbose_name="localização")
    rejected_orders = models.IntegerField(default=0, verbose_name="Pedidos Rejeitados")

    class Meta:
        verbose_name = "Motorista"
        verbose_name_plural = "Motoristas"

    def __str__(self):
        return self.user.get_username()

    def increment_rejected_orders(self):
        self.rejected_orders += 1
        self.save()

    def send_rejection_warning_email(self):
        if self.rejected_orders >= 10:
            logger.info(f"Sending rejection warning email for driver {self.id}")
            context = {
                "driver_name": self.user.get_full_name(),
                "rejected_count": self.rejected_orders,
            }
            subject = "Aviso: Você atingiu o limite de rejeições de pedidos"
            message = render_to_string("email_templates/rejection_warning.html", context)
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
            )
            email.content_subtype = "html"
            email.send()
            logger.info(f"Rejection warning email sent for driver {self.id}")
