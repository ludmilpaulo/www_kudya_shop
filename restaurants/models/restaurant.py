from django.db import models
from datetime import date, datetime, time
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from django.template.loader import render_to_string
import logging

from order.models import Order
from order.utils import generate_invoice

logger = logging.getLogger(__name__)

User = get_user_model()

class RestaurantCategory(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    image = models.ImageField(upload_to='category/', blank=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='usuário', blank=True)
    category = models.ForeignKey(RestaurantCategory, related_name='restaurant', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=500, verbose_name='Nome do restaurante')
    phone = models.CharField(max_length=500, verbose_name='Telefone do restaurante')
    address = models.CharField(max_length=500, verbose_name='Endereço do restaurante')
    logo = models.ImageField(upload_to='restaurant_logo/', blank=False, verbose_name='Logotipo do restaurante')
    location = models.CharField(max_length=500, blank=True, verbose_name='localização')
    restaurant_license = models.FileField(upload_to='vendor/license', blank=True, verbose_name='Licenca do restaurante')
    barnner = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def activate(self):
        self.is_approved = True
        self.save()
        self.send_approval_email()

    def deactivate(self):
        self.is_approved = False
        self.save()
        self.send_rejection_email()

    def get_orders(self, period):
        if period == 'weekly':
            start_date = timezone.now() - timezone.timedelta(days=7)
        elif period == 'monthly':
            start_date = timezone.now() - timezone.timedelta(days=30)
        else:
            start_date = timezone.now() - timezone.timedelta(days=1)

        orders = Order.objects.filter(restaurant=self, created_at__gte=start_date)
        return orders

    def generate_invoice(self, period):
        orders = self.get_orders(period)
        total_amount = orders.aggregate(Sum('total'))['total__sum']
        context = {
            'restaurant': self,
            'orders': orders,
            'total_amount': total_amount,
            'period': period,
        }
        pdf_path, pdf_content = generate_invoice(context)
        return pdf_path, pdf_content

    def __str__(self):
        return self.name

    def is_open(self):
        # Check current day's opening hours.
        today_date = date.today()
        today = today_date.isoweekday()

        current_opening_hours = OpeningHour.objects.filter(restaurant=self, day=today)
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
        if self.pk is None:
            self.send_signup_email()
        super(Restaurant, self).save(*args, **kwargs)

    def send_signup_email(self):
        """Send a sign-up confirmation email."""
        subject = 'Bem-vindo ao nossa plataforma!'
        message = render_to_string('email_templates/welcome_email.html', {'user': self.user, 'restaurant': self})
        email_from = settings.EMAIL_HOST_USER
        try:
            send_mail(subject, message, email_from, [self.user.email])
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def send_approval_email(self):
        """Send an approval email."""
        context = {'user': self.user, 'restaurant': self}
        mail_subject = "Parabéns! Seu restaurante foi aprovado."
        message = render_to_string('email_templates/approval_email.html', context)
        try:
            send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [self.user.email])
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def send_rejection_email(self):
        """Send a rejection email."""
        context = {'user': self.user, 'restaurant': self}
        mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
        message = render_to_string('email_templates/rejection_email.html', context)
        try:
            send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [self.user.email])
        except Exception as e:
            logger.error(f"Error sending email: {e}")

DAYS = [
    (1, "Segunda-feira"),
    (2, "Terça-feira"),
    (3, "Quarta-feira"),
    (4, "Quinta-feira"),
    (5, "Sexta-feira"),
    (6, "Sábado"),
    (7, "Domingo"),
]

HOUR_OF_DAY_24 = [(time(h, m).strftime('%I:%M %p'), time(h, m).strftime('%I:%M %p')) for h in range(24) for m in (0, 30)]

class OpeningHour(models.Model):
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS)
    from_hour = models.CharField(choices=HOUR_OF_DAY_24, max_length=10, blank=True)
    to_hour = models.CharField(choices=HOUR_OF_DAY_24, max_length=10, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ('day', '-from_hour')
        unique_together = ('restaurant', 'day', 'from_hour', 'to_hour')

    def __str__(self):
        return f"{self.get_day_display()} {self.from_hour} - {self.to_hour}"
