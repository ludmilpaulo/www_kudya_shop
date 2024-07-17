from django.contrib.auth import get_user_model
from curtomers.models import Customer
from drivers.models import Driver
from drivers.serializers import DriverSerializer
from order.models import Order
from restaurants.models import Meal
from django.db.models import Sum, Count, Case, When
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, get_current_timezone

User = get_user_model()

@api_view(["GET"])
def restaurant_report(request, user_id):
    try:
        # Get the user object
        user = User.objects.get(id=user_id)
        restaurant = user.restaurant  # Assuming user has a restaurant attribute

        # Get the timeframe parameter
        timeframe = request.GET.get('timeframe', 'week')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Initialize the revenue and orders lists
        revenue = []
        orders = []

        if timeframe == 'day':
            # Calculate hourly data for the current day
            today = datetime.now()
            current_day_hours = [today.replace(hour=i, minute=0, second=0, microsecond=0) for i in range(24)]

            for hour in current_day_hours:
                next_hour = hour + timedelta(hours=1)
                delivered_orders = Order.objects.filter(
                    restaurant=restaurant,
                    status=Order.DELIVERED,
                    created_at__gte=make_aware(hour),
                    created_at__lt=make_aware(next_hour)
                )
                revenue.append(sum(order.total for order in delivered_orders))
                orders.append(delivered_orders.count())

        elif timeframe == 'week':
            # Calculate daily data for the current week
            today = datetime.now()
            current_weekdays = [today + timedelta(days=i) for i in range(0 - today.weekday(), 7 - today.weekday())]

            for day in current_weekdays:
                delivered_orders = Order.objects.filter(
                    restaurant=restaurant,
                    status=Order.DELIVERED,
                    created_at__year=day.year,
                    created_at__month=day.month,
                    created_at__day=day.day
                )
                revenue.append(sum(order.total for order in delivered_orders))
                orders.append(delivered_orders.count())

        elif timeframe == 'month':
            # Calculate daily data for the current month
            today = datetime.now()
            current_month_days = [today.replace(day=i) for i in range(1, 32) if (today.replace(day=i)).month == today.month]

            for day in current_month_days:
                delivered_orders = Order.objects.filter(
                    restaurant=restaurant,
                    status=Order.DELIVERED,
                    created_at__year=day.year,
                    created_at__month=day.month,
                    created_at__day=day.day
                )
                revenue.append(sum(order.total for order in delivered_orders))
                orders.append(delivered_orders.count())

        elif timeframe == 'custom' and start_date and end_date:
            # Calculate daily data for the custom date range
            start_date = make_aware(datetime.fromisoformat(start_date))
            end_date = make_aware(datetime.fromisoformat(end_date))

            current_range_days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

            for day in current_range_days:
                delivered_orders = Order.objects.filter(
                    restaurant=restaurant,
                    status=Order.DELIVERED,
                    created_at__year=day.year,
                    created_at__month=day.month,
                    created_at__day=day.day
                )
                revenue.append(sum(order.total for order in delivered_orders))
                orders.append(delivered_orders.count())

        # Top 3 Meals
        top3_meals = (
            Meal.objects.filter(restaurant=restaurant)
            .annotate(total_order=Sum("orderdetails__quantity"))
            .order_by("-total_order")[:3]
        )

        meals_data = {
            "labels": [meal.name for meal in top3_meals],
            "data": [meal.total_order or 0 for meal in top3_meals],
        }

        # Top 3 Drivers
        top3_drivers = Driver.objects.annotate(
            total_order=Count(Case(When(order__restaurant=restaurant, then=1)))
        ).order_by("-total_order")[:3]

        drivers_data = {
            "labels": [driver.user.get_full_name() for driver in top3_drivers],
            "data": [driver.total_order for driver in top3_drivers],
        }

        # Top 3 Customers
        top3_customers = Customer.objects.annotate(
            total_order=Count(Case(When(order__restaurant=restaurant, then=1)))
        ).order_by("-total_order")[:3]

        customers_data = {
            "labels": [customer.user.get_full_name() for customer in top3_customers],
            "data": [customer.total_order for customer in top3_customers],
        }

        # Total amounts
        total_restaurant_amount = sum(revenue)
        total_paid_amount = sum(order.original_price for order in Order.objects.filter(
            restaurant=restaurant,
            payment_status_restaurant=Order.PAID,
        ))

        proof_of_payment = ""
        if total_paid_amount > 0:
            latest_paid_order = Order.objects.filter(
                restaurant=restaurant,
                payment_status_restaurant=Order.PAID,
            ).order_by('-created_at').first()
            proof_of_payment = latest_paid_order.proof_of_payment_restaurant.url if latest_paid_order.proof_of_payment_restaurant else ""

        # Return the data as JSON response
        return Response(
            {
                "revenue": revenue,
                "orders": orders,
                "meals": meals_data,
                "drivers": drivers_data,
                "customers": customers_data,
                "total_restaurant_amount": total_restaurant_amount,
                "total_paid_amount": total_paid_amount,
                "proof_of_payment": proof_of_payment,
            }
        )

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    except Exception as e:
        # Handle exceptions and return appropriate response
        return Response({"error": str(e)}, status=500)
