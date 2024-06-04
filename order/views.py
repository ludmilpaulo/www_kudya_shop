from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import urllib.parse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from curtomers.models import Customer
from order.models import Order, OrderDetails, send_order_email
from order.utils import generate_pdf
from django.shortcuts import get_object_or_404
from restaurants.models import Meal, Restaurant
from restaurants.serializers import RestaurantSerializer

@csrf_exempt
@api_view(['POST'])
def customer_add_order(request):
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

    # Get profile
    customer = Customer.objects.get(user=access)

    if Order.objects.filter(customer=customer).exclude(
            status=Order.DELIVERED):
        return Response({
            "error": "failed",
            "status": "Seu último pedido deve ser entregue para Pedir Outro."
        })

    # Check Address
    if not data['address']:
        return Response({
            "status": "failed",
            "error": "Address is required."
        })

    # Get Order Details
    order_details = data["order_details"]
    order_total = 0
    for meal in order_details:
        order_total += Meal.objects.get(
            id=meal["meal_id"]).price * meal["quantity"]

    if len(order_details) > 0:
        # Step 2 - Create an Order
        order = Order.objects.create(
            customer=customer,
            restaurant_id=data["restaurant_id"],
            total=order_total,
            status=Order.COOKING,
            address=data["address"],
            payment_method=data.get("payment_method", "not specified")  # Store payment method
        )

        # Step 3 - Create Order details
        for meal in order_details:
            OrderDetails.objects.create(
                order=order,
                meal_id=meal["meal_id"],
                quantity=meal["quantity"],
                sub_total=Meal.objects.get(id=meal["meal_id"]).price *
                meal["quantity"])

        # Send email notifications
        send_order_email(customer.user.email, order)
        restaurant_email = order.restaurant.user.email
        send_order_email(restaurant_email, order, is_restaurant=True)

        # Generate WhatsApp URL
        phone_number = "customer_phone_number"  # Replace with the actual phone number
        message = f"Olá {customer.user.get_full_name()}, seu pedido foi recebido com sucesso. Seu PIN secreto é {order.secret_pin}."
        whatsapp_url = f"https://wa.me/{phone_number}?text={urllib.parse.quote(message)}"

        return Response({"status": "success", "secret_pin": order.secret_pin, "whatsapp_url": whatsapp_url})
    else:
        return Response({
            "status": "failed",
            "error": "Failed connect to Stripe."
        })


@api_view(['GET'])
def generate_invoices(request):
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