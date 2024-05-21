from django.utils import timezone
from django.contrib.auth import get_user_model
from curtomers.models import Customer
from drivers.models import Driver
from rest_framework.decorators import api_view
from rest_framework.response import Response

from order.models import Order
from django.db.models import Count, Sum, Case, When

from restaurants.models import Meal






User = get_user_model()

@api_view(['GET'])
def shop_report(request, user_id):
    try:
        # Get the user object
        user = User.objects.get(id=user_id)
        restaurant = user.restaurant  # Assuming user has a shop attribute

        # Calculate revenue and number of orders for the current week
        from datetime import datetime, timedelta

        revenue = []
        orders = []

        # Calculate weekdays
        today = datetime.now()
        current_weekdays = [
            today + timedelta(days=i)
            for i in range(0 - today.weekday(), 7 - today.weekday())
        ]

        for day in current_weekdays:
            delivered_orders = Order.objects.filter(
                restaurant=restaurant,
                status=Order.DELIVERED,
                created_at__year=day.year,
                created_at__month=day.month,
                created_at__day=day.day)
            revenue.append(sum(order.total for order in delivered_orders))
            orders.append(delivered_orders.count())

        # Top 3 Products
        top3_meals = Meal.objects.filter(restaurant=restaurant)\
            .annotate(total_order=Sum('orderdetails__quantity'))\
            .order_by("-total_order")[:3]

        meal_data = {
            "labels": [meal.title for meal in top3_meals],
            "data": [meal.total_order or 0 for meal in top3_meals]
        }

        # Top 3 Drivers
        top3_drivers = Driver.objects.annotate(total_order=Count(
            Case(When(order__restaurant=restaurant, then=1)))).order_by("-total_order")[:3]

        drivers_data = {
            "labels": [driver.user.get_full_name() for driver in top3_drivers],
            "data": [driver.total_order for driver in top3_drivers]
        }

        # Top 3 Customers
        top3_customers = Customer.objects.annotate(total_order=Count(
            Case(When(order__restaurant=restaurant, then=1)))).order_by("-total_order")[:3]

        customers_data = {
            "labels": [customer.user.get_full_name() for customer in top3_customers],
            "data": [customer.total_order for customer in top3_customers]
        }

        # Return the data as JSON response
        return Response({
            "revenue": revenue,
            "orders": orders,
            "meals": meal_data,
            "drivers": drivers_data,
            "customers": customers_data
        })

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    except Exception as e:
        # Handle exceptions and return appropriate response
        return Response({"error": str(e)}, status=500)
    
    
    


@api_view(['GET'])
def shop_customers(request, user_id):
    user = User.objects.get(id=user_id)
    shop = user.shop  # Assuming user has a foreign key relationship with Shop model
    customers = Customer.objects.annotate(
        total_order=Count(
            Case(When(order__shop=shop, then=1))
        )
    ).order_by("-total_order")

    all_customers = [
        customer for customer in customers if customer.total_order > 0
    ]

    serializer = CustomerSerializer(all_customers, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def shop_drivers(request, user_id):
    user = User.objects.get(id=user_id)
    shop = user.shop 
    drivers = Driver.objects.annotate(
        total_order=Count(
            Case(When(order__shop=shop, then=1))
        )
    ).order_by("-total_order")

    all_drivers = [driver for driver in drivers if driver.total_order > 0]

    serializer = DriverSerializer(all_drivers, many=True)
    return Response(serializer.data)


