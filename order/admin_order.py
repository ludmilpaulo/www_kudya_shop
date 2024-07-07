from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from order.email_utils import send_order_email
from order.models import Order, OrderDetails
from order.utils import generate_invoice
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.core.files.base import ContentFile
import urllib.parse
import logging

from restaurants.models import Meal

logger = logging.getLogger(__name__)



@csrf_exempt
def upload_proof_of_payment_restaurant(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            proof_of_payment_file = request.FILES['proof_of_payment']
            order.proof_of_payment_restaurant.save(proof_of_payment_file.name, proof_of_payment_file)
            order.payment_status_restaurant = Order.PAID
            order.save()
            return JsonResponse({'status': 'success', 'message': 'Proof of payment to restaurant uploaded successfully'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'message': 'Error uploading proof of payment'}, status=400)
    return JsonResponse({'status': 'fail', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def upload_proof_of_payment_driver(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            proof_of_payment_file = request.FILES['proof_of_payment']
            order.proof_of_payment_driver.save(proof_of_payment_file.name, proof_of_payment_file)
            order.payment_status_driver = Order.PAID
            order.save()
            return JsonResponse({'status': 'success', 'message': 'Proof of payment to driver uploaded successfully'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'message': 'Error uploading proof of payment'}, status=400)
    return JsonResponse({'status': 'fail', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def mark_as_paid(request, type, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            if type == 'restaurant':
                order.payment_status_restaurant = Order.PAID
            elif type == 'driver':
                order.payment_status_driver = Order.PAID
            order.save()
            return JsonResponse({'status': 'success', 'message': f'Order {type} marked as paid'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'message': 'Error marking as paid'}, status=400)
    return JsonResponse({'status': 'fail', 'message': 'Invalid request'}, status=400)

def get_orders(request):
    filter_by = request.GET.get('filter_by', 'all')
    today = timezone.now()

    if filter_by == 'day':
        start_date = today - timedelta(days=1)
    elif filter_by == 'week':
        start_date = today - timedelta(weeks=1)
    elif filter_by == 'month':
        start_date = today - timedelta(days=30)
    else:
        start_date = None

    if start_date:
        orders = Order.objects.filter(created_at__gte=start_date)
    else:
        orders = Order.objects.all()

    orders_data = [
        {
            'id': order.id,
            'customer': order.customer.user.get_full_name(),
            'restaurant': order.restaurant.name,
            'status': order.get_status_display(),
            'total': order.total,
            'created_at': order.created_at,
            'invoice_pdf': order.invoice_pdf.url if order.invoice_pdf else None,
            'payment_status_restaurant': order.payment_status_restaurant,
            'payment_status_driver': order.payment_status_driver,
            'original_price': order.original_price,
            'driver_commission': order.calculate_driver_commission(),
        }
        for order in orders
    ]

    return JsonResponse({'orders': orders_data})
