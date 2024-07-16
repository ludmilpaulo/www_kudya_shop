from django.contrib.auth import get_user_model


from curtomers.models import Customer
from curtomers.serializers import CustomerSerializer
from drivers.models import Driver
from drivers.serializers import DriverSerializer
from order.models import Order


from restaurants.models import Meal


User = get_user_model()

from django.db.models import Sum, Count, Case, When
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, get_current_timezone


@api_view(["GET"])
def restaurant_report(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        restaurant = user.restaurant

        timeframe = request.query_params.get('timeframe', 'week')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date and end_date:
            start_date = make_aware(datetime.fromisoformat(start_date.replace('Z', '+00:00')))
            end_date = make_aware(datetime.fromisoformat(end_date.replace('Z', '+00:00')))
        else:
            today = make_aware(datetime.now(), get_current_timezone())
            if timeframe == 'day':
                start_date = today - timedelta(days=1)
                end_date = today
            elif timeframe == 'month':
                start_date = today - timedelta(days=30)
                end_date = today
            else:
                start_date = today - timedelta(days=7)
                end_date = today

        delivered_orders = Order.objects.filter(
            restaurant=restaurant,
            status=Order.DELIVERED,
            created_at__range=[start_date, end_date]
        )

        revenue = []
        orders = []
        total_restaurant_amount = 0
        current_days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        for day in current_days:
            day_orders = delivered_orders.filter(
                created_at__year=day.year,
                created_at__month=day.month,
                created_at__day=day.day,
            )
            revenue.append(sum(order.total for order in day_orders))
            orders.append(day_orders.count())
            for order in day_orders:
                total_restaurant_amount += order.original_price

        if not any(revenue) and not any(orders):
            return Response({"message": "No sales data available for the selected dates"}, status=200)

        top3_meals = (
            Meal.objects.filter(restaurant=restaurant)
            .annotate(total_order=Sum("orderdetails__quantity"))
            .order_by("-total_order")[:3]
        )
        meals_data = {
            "labels": [meal.name for meal in top3_meals],
            "data": [meal.total_order or 0 for meal in top3_meals],
        }

        top3_drivers = Driver.objects.annotate(
            total_order=Count(Case(When(order__restaurant=restaurant, then=1)))
        ).order_by("-total_order")[:3]
        drivers_data = {
            "labels": [driver.user.get_full_name() for driver in top3_drivers],
            "data": [driver.total_order for driver in top3_drivers],
        }

        top3_customers = Customer.objects.annotate(
            total_order=Count(Case(When(order__restaurant=restaurant, then=1)))
        ).order_by("-total_order")[:3]
        customers_data = {
            "labels": [customer.user.get_full_name() for customer in top3_customers],
            "data": [customer.total_order for customer in top3_customers],
        }

        return Response(
            {
                "revenue": revenue,
                "orders": orders,
                "meals": meals_data,
                "drivers": drivers_data,
                "customers": customers_data,
                "total_restaurant_amount": total_restaurant_amount,
            }
        )

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
