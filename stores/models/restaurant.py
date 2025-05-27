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

logger = logging.getLogger(__name__)

User = get_user_model()




DAYS = [
    (1, "Segunda-feira"),
    (2, "Terça-feira"),
    (3, "Quarta-feira"),
    (4, "Quinta-feira"),
    (5, "Sexta-feira"),
    (6, "Sábado"),
    (7, "Domingo"),
]

HOUR_OF_DAY_24 = [
    (time(h, m).strftime("%I:%M %p"), time(h, m).strftime("%I:%M %p"))
    for h in range(24)
    for m in (0, 30)
]


class OpeningHour(models.Model):
    store = models.ForeignKey("store", on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS)
    from_hour = models.CharField(choices=HOUR_OF_DAY_24, max_length=10, blank=True)
    to_hour = models.CharField(choices=HOUR_OF_DAY_24, max_length=10, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ("day", "-from_hour")
        unique_together = ("store", "day", "from_hour", "to_hour")

    def __str__(self):
        return f"{self.get_day_display()} {self.from_hour} - {self.to_hour}"
