from django.db import models
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from datetime import timedelta, datetime
import random
import string

# Import your existing models
from restaurants.models import Restaurant, Meal
from django.contrib.auth import get_user_model

User = get_user_model()


4



class RestaurantUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=1)

    def calculate_user_commission(self, order_total):
        return order_total * (self.commission_percentage / 100)

    def generate_user_invoice(self, orders):
        total_commission = sum([self.calculate_user_commission(order.total) for order in orders])
        context = {
            'user': self.user,
            'restaurant': self.restaurant,
            'orders': orders,
            'total_commission': total_commission,
        }
        html_string = render_to_string('user_invoice_template.html', context)
        html = HTML(string=html_string)
        pdf_content = html.write_pdf(stylesheets=[CSS(string=self.invoice_css())])
        return "path/to/user_invoice.pdf", pdf_content

    def invoice_css(self):
        return """
        body {
          font-family: Arial, sans-serif;
          background-color: #f4f4f4;
          color: #333;
          padding: 20px;
        }
        .container {
          background-color: #fff;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .header {
          text-align: center;
          background: linear-gradient(to right, #facc15, #2563eb);
          padding: 10px 0;
          border-radius: 8px 8px 0 0;
        }
        .header img {
          max-width: 150px;
        }
        .content {
          margin-top: 20px;
        }
        .content h2 {
          color: #2563eb;
        }
        .table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 20px;
        }
        .table th, .table td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        .table th {
          background-color: #2563eb;
          color: #fff;
        }
        .footer {
          margin-top: 20px;
          text-align: center;
          font-size: 12px;
          color: #777;
        }
        """
