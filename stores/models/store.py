from django.db import models
from datetime import date, datetime, time
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from django.template.loader import render_to_string
import logging
from order.models import Order
from order.utils import generate_invoice
from stores.models.restaurant import OpeningHour

logger = logging.getLogger(__name__)

User = get_user_model()

class StoreType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to="store_type_icons/", blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Store Type"
        verbose_name_plural = "Store Types"

    def __str__(self):
        return self.name


class StoreCategory(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    image = models.ImageField(upload_to="category/", blank=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Store Category"
        verbose_name_plural = "Store Categories"

    def __str__(self):
        return self.name


class Store(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="usuário", blank=True)
    store_type = models.ForeignKey(StoreType, on_delete=models.SET_NULL, null=True, related_name="stores")
    category = models.ForeignKey(StoreCategory, related_name="stores", on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=500)
    phone = models.CharField(max_length=500)
    address = models.CharField(max_length=500)
    logo = models.ImageField(upload_to="store_logos/")
    bank = models.CharField(max_length=500, blank=True, verbose_name="bank")
    account_number = models.CharField(max_length=500, blank=True, verbose_name="account")
    iban = models.CharField(max_length=500, blank=True, verbose_name="iban")
    location = models.CharField(max_length=500, blank=True)
    license = models.FileField(upload_to="vendor/license", blank=True)
    banner = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    def activate(self):
        if not self.is_approved:
            self.is_approved = True
            self.save()
            self.send_approval_email()

    def deactivate(self):
        if self.is_approved:
            self.is_approved = False
            self.save()
            self.send_rejection_email()

    def get_orders(self, period):
        if period == "weekly":
            start_date = timezone.now() - timezone.timedelta(days=7)
        elif period == "monthly":
            start_date = timezone.now() - timezone.timedelta(days=30)
        else:
            start_date = timezone.now() - timezone.timedelta(days=1)

        orders = Order.objects.filter(store=self, created_at__gte=start_date)
        return orders

    def generate_invoice(self, period):
        orders = self.get_orders(period)
        total_amount = orders.aggregate(Sum("total"))["total__sum"]
        context = {
            "store": self,
            "orders": orders,
            "total_amount": total_amount,
            "period": period,
        }
        pdf_path, pdf_content = generate_invoice(context)
        return pdf_path, pdf_content

    def __str__(self):
        return self.name

    def is_open(self):
        today_date = date.today()
        today = today_date.isoweekday()

        current_opening_hours = OpeningHour.objects.filter(store=self, day=today)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        is_open = None
        for i in current_opening_hours:
            if not i.is_closed:
                start = str(datetime.strptime(i.from_hour, "%I:%M %p").time())
                end = str(datetime.strptime(i.to_hour, "%I:%M %p").time())
                if start < current_time < end:
                    is_open = True
                    break
                else:
                    is_open = False
        return is_open

    def save(self, *args, **kwargs):
        new_store = self.pk is None
        super(Store, self).save(*args, **kwargs)
        if new_store:
            self.send_signup_email()

    def send_signup_email(self):
        subject = "Bem-vindo ao nossa plataforma!"
        message = render_to_string(
            "email_templates/welcome_email.html",
            {"user": self.user, "store": self},
        )
        email_from = settings.EMAIL_HOST_USER
        try:
            email = EmailMessage(subject, message, email_from, [self.user.email])
            email.content_subtype = "html"  # Set the email content type to HTML
            email.send()
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def send_approval_email(self):
        context = {"user": self.user, "store": self}
        mail_subject = "Parabéns! Seu storee foi aprovado."
        message = render_to_string("email_templates/approval_email.html", context)
        try:
            email = EmailMessage(
                mail_subject, message, settings.EMAIL_HOST_USER, [self.user.email]
            )
            email.content_subtype = "html"  # Set the email content type to HTML
            email.send()
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def send_rejection_email(self):
        context = {"user": self.user, "store": self}
        mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
        message = render_to_string("email_templates/rejection_email.html", context)
        try:
            email = EmailMessage(
                mail_subject, message, settings.EMAIL_HOST_USER, [self.user.email]
            )
            email.content_subtype = "html"  # Set the email content type to HTML
            email.send()
        except Exception as e:
            logger.error(f"Error sending email: {e}")


