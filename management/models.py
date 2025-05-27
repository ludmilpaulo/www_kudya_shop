from django.db import models
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from datetime import timedelta, datetime
import random
import string
from django.db.models import Sum

# Import your existing models
from order.utils import generate_invoice
from stores.models import Store, Product
from django.contrib.auth import get_user_model

User = get_user_model()


class Partner(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="partners")
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="partners"
    )
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_earnings(self, period):
        orders = self.store.get_orders(period)
        total_earnings = (
            orders.aggregate(Sum("total"))["total__sum"] * 0.01
        )  # 1% earnings
        self.earnings += total_earnings
        self.save()

    def generate_invoice(self, period):
        self.calculate_earnings(period)
        context = {
            "partner": self,
            "total_earnings": self.earnings,
            "period": period,
        }
        pdf_path, pdf_content = generate_invoice(context)
        return pdf_path, pdf_content

    def __str__(self):
        return f"{self.user.username} - {self.store.name}"
