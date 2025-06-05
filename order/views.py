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
from customers.models import Customer
from order.models import Order, OrderDetails
from stores.models import Product, Store
from stores.serializers import StoreSerializer
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from .utils import generate_invoice, generate_pdf


@api_view(["GET"])
def generate_store_invoices(request):
    if "store_id" not in request.GET:
        return Response({"error": "store ID is required."})

    store_id = request.GET["store_id"]
    store = Store.objects.get(id=store_id)

    period = request.GET.get("period", "weekly")  # 'weekly' or 'monthly'

    if period == "weekly":
        start_date = timezone.now() - timedelta(days=7)
    else:
        start_date = timezone.now() - timedelta(days=30)

    orders = Order.objects.filter(
        store=store, created_at__gte=start_date
    ).annotate(order_total=Sum("order_details__sub_total"))

    context = {
        "store_name": store.name,
        "orders": orders,
        "period": "Semana" if period == "weekly" else "Mês",
    }

    pdf = generate_pdf("email_templates/store_invoice.html", context)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{period}.pdf"'
    return response


@api_view(["GET"])
def store_details(request, store_id):
    store = get_object_or_404(store, pk=store_id)
    serializer = StoreSerializer(store, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)
