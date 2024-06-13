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
import logging
logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
def customer_add_order(request):
    data = request.data
    try:
        access = Token.objects.get(key=data['access_token']).user
    except Token.DoesNotExist:
        return Response({"status": "failed", "error": "Invalid access token."})

    logger.info(f"Received order data: {data}")

    # Get profile
    try:
        customer = Customer.objects.get(user=access)
    except Customer.DoesNotExist:
        return Response({"status": "failed", "error": "Customer profile not found."})

    # Check for existing orders to the same restaurant that are not delivered
    existing_orders = Order.objects.filter(customer=customer, restaurant_id=data["restaurant_id"]).exclude(status=Order.DELIVERED)
    if existing_orders.exists():
        return Response({"status": "failed", "error": "Seu último pedido deve ser entregue para Pedir Outro."})

    # Check Address
    if not data.get('address'):
        return Response({"status": "failed", "error": "Address is required."})

    # Get Order Details
    order_details = data.get("order_details", [])
    if not order_details:
        return Response({"status": "failed", "error": "Order details are required."})

    order_total = 0
    for meal in order_details:
        try:
            meal_obj = Meal.objects.get(id=meal["meal_id"])
            order_total += meal_obj.price * meal["quantity"]
        except Meal.DoesNotExist:
            return Response({"status": "failed", "error": f"Meal with ID {meal['meal_id']} not found."})

    # Step 2 - Create an Order
    try:
        order = Order.objects.create(
            customer=customer,
            restaurant_id=data["restaurant_id"],
            total=order_total,
            status=Order.COOKING,
            address=data["address"],
            payment_method=data["payment_method"]
        )
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return Response({"status": "failed", "error": "Error creating order."})

    # Step 3 - Create Order details
    for meal in order_details:
        try:
            OrderDetails.objects.create(
                order=order,
                meal_id=meal["meal_id"],
                quantity=meal["quantity"],
                sub_total=meal_obj.price * meal["quantity"]
            )
        except Exception as e:
            logger.error(f"Error creating order details: {e}")
            return Response({"status": "failed", "error": "Error creating order details."})

    # Generate invoice
    try:
        pdf_path, pdf_content = generate_invoice(order)
        order.invoice_pdf.save(f"order_{order.id}.pdf", ContentFile(pdf_content), save=False)
        order.save()
    except Exception as e:
        logger.error(f"Error generating invoice: {e}")
        return Response({"status": "failed", "error": "Error generating invoice."})

    try:
        # Send email notifications
        send_order_email(to_email=customer.user.email, order=order, pdf_path=pdf_path, pdf_content=pdf_content)
        restaurant_email = order.restaurant.user.email
        send_order_email(to_email=restaurant_email, order=order, pdf_path=pdf_path, pdf_content=pdf_content, is_restaurant=True)
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return Response({"status": "failed", "error": "Erro ao enviar email. Por favor, tente novamente."})

    # Generate WhatsApp URL
    phone_number = customer.phone # Replace with the actual phone number
    message = f"Olá {customer.user.get_full_name()}, seu pedido foi recebido com sucesso. Seu PIN secreto é {order.secret_pin}."
    whatsapp_url = f"https://wa.me/{phone_number}?text={urllib.parse.quote(message)}"

    return Response({"status": "success", "secret_pin": order.secret_pin, "whatsapp_url": whatsapp_url})

@api_view(['GET'])
def generate_restaurant_invoices(request):
    if 'restaurant_id' not in request.GET:
        return Response({"error": "Restaurant ID is required."})

    restaurant_id = request.GET['restaurant_id']
    restaurant = Restaurant.objects.get(id=restaurant_id)

    period = request.GET.get('period', 'weekly')  # 'weekly' or 'monthly'

    if period == 'weekly':
        start_date = timezone.now() - timedelta(days=7)
    else:
        start_date = timezone.now() - timedelta(days=30)

    orders = Order.objects.filter(
        restaurant=restaurant,
        created_at__gte=start_date
    ).annotate(
        order_total=Sum('order_details__sub_total')
    )

    context = {
        'restaurant_name': restaurant.name,
        'orders': orders,
        'period': 'Semana' if period == 'weekly' else 'Mês'
    }

    pdf = generate_pdf('email_templates/restaurant_invoice.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{period}.pdf"'
    return response

@api_view(['GET'])
def restaurant_details(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    serializer = RestaurantSerializer(restaurant, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
