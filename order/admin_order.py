from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from .models import Order

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
            'invoice_pdf': order.invoice_pdf.url if order.invoice_pdf else None
        }
        for order in orders
    ]
    
    return JsonResponse({'orders': orders_data})


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.base import ContentFile
from .models import Order

@csrf_exempt
def upload_proof_of_payment_restaurant(request, order_id):
    if request.method == 'POST':
        order = Order.objects.get(id=order_id)
        proof_of_payment_file = request.FILES['proof_of_payment']
        order.proof_of_payment_restaurant.save(proof_of_payment_file.name, proof_of_payment_file)
        order.payment_status_restaurant = Order.PAID
        order.save()
        return JsonResponse({'status': 'success', 'message': 'Proof of payment to restaurant uploaded successfully'})
    return JsonResponse({'status': 'fail', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def upload_proof_of_payment_driver(request, order_id):
    if request.method == 'POST':
        order = Order.objects.get(id=order_id)
        proof_of_payment_file = request.FILES['proof_of_payment']
        order.proof_of_payment_driver.save(proof_of_payment_file.name, proof_of_payment_file)
        order.payment_status_driver = Order.PAID
        order.save()
        return JsonResponse({'status': 'success', 'message': 'Proof of payment to driver uploaded successfully'})
    return JsonResponse({'status': 'fail', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def mark_as_paid(request, type, order_id):
    if request.method == 'POST':
        order = Order.objects.get(id=order_id)
        if type == 'restaurant':
            order.payment_status_restaurant = Order.PAID
        elif type == 'driver':
            order.payment_status_driver = Order.PAID
        order.save()
        return JsonResponse({'status': 'success', 'message': f'Order {type} marked as paid'})
    return JsonResponse({'status': 'fail', 'message': 'Invalid request'}, status=400)