from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse
from order.email_utils import send_order_email
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import urllib.parse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from curtomers.models import Customer
from order.models import Order, OrderDetails
from restaurants.models import Meal, Restaurant
from restaurants.serializers import RestaurantSerializer
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from .utils import generate_invoice, generate_pdf


@api_view(["GET"])
def generate_restaurant_invoices(request):
    if "restaurant_id" not in request.GET:
        return Response({"error": "Restaurant ID is required."})

    restaurant_id = request.GET["restaurant_id"]
    restaurant = Restaurant.objects.get(id=restaurant_id)

    period = request.GET.get("period", "weekly")  # 'weekly' or 'monthly'

    if period == "weekly":
        start_date = timezone.now() - timedelta(days=7)
    else:
        start_date = timezone.now() - timedelta(days=30)

    orders = Order.objects.filter(
        restaurant=restaurant, created_at__gte=start_date
    ).annotate(order_total=Sum("order_details__sub_total"))

    context = {
        "restaurant_name": restaurant.name,
        "orders": orders,
        "period": "Semana" if period == "weekly" else "Mês",
    }

    pdf = generate_pdf("email_templates/restaurant_invoice.html", context)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{period}.pdf"'
    return response


@api_view(["GET"])
def restaurant_details(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    serializer = RestaurantSerializer(restaurant, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)
