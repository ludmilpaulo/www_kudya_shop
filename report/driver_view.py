from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from drivers.models import Driver
from order.models import Order

@api_view(["POST"])
def driver_commission_revenue(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    driver = Driver.objects.get(user=access)

    filter_type = data.get("filter_type", "week")  # default to week
    custom_start_date = data.get("start_date")
    custom_end_date = data.get("end_date")

    revenue = {}
    paid_orders = []
    unpaid_orders = []

    today = timezone.now()
    if filter_type == "day":
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif filter_type == "month":
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = (start_date + timedelta(days=32)).replace(day=1)
    elif filter_type == "custom" and custom_start_date and custom_end_date:
        start_date = datetime.strptime(custom_start_date, "%Y-%m-%d")
        end_date = datetime.strptime(custom_end_date, "%Y-%m-%d") + timedelta(days=1)
    else:  # default to week
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)

    # Ensure dates are timezone-aware
    start_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
    end_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date

    orders = Order.objects.filter(
        driver=driver,
        status=Order.DELIVERED,
        created_at__gte=start_date,
        created_at__lt=end_date,
    )

    # Calculate earnings and categorize orders based on payment status
    if filter_type == "day":
        for hour in range(24):
            hour_start = start_date + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            hour_orders = orders.filter(created_at__gte=hour_start, created_at__lt=hour_end)
            total_earnings = sum(order.driver_commission + order.delivery_fee for order in hour_orders)
            revenue[hour_start.strftime("%H:%M")] = total_earnings
    elif filter_type == "week":
        for day in range(7):
            day_date = start_date + timedelta(days=day)
            day_orders = orders.filter(
                created_at__year=day_date.year,
                created_at__month=day_date.month,
                created_at__day=day_date.day,
            )
            total_earnings = sum(order.driver_commission + order.delivery_fee for order in day_orders)
            revenue[day_date.strftime("%a")] = total_earnings
    elif filter_type == "month":
        for day in range((end_date - start_date).days):
            day_date = start_date + timedelta(days=day)
            day_orders = orders.filter(
                created_at__year=day_date.year,
                created_at__month=day_date.month,
                created_at__day=day_date.day,
            )
            total_earnings = sum(order.driver_commission + order.delivery_fee for order in day_orders)
            revenue[day_date.strftime("%d/%m")] = total_earnings
    elif filter_type == "custom":
        for day in range((end_date - start_date).days):
            day_date = start_date + timedelta(days=day)
            day_orders = orders.filter(
                created_at__year=day_date.year,
                created_at__month=day_date.month,
                created_at__day=day_date.day,
            )
            total_earnings = sum(order.driver_commission + order.delivery_fee for order in day_orders)
            revenue[day_date.strftime("%Y-%m-%d")] = total_earnings

    # Categorize orders into paid and unpaid
    for order in orders:
        order_data = {
            "order_id": order.id,
            "amount": order.driver_commission + order.delivery_fee,
            "proof_of_payment": order.proof_of_payment_driver.url if order.proof_of_payment_driver else None
        }
        if order.payment_status_driver == Order.PAID:
            paid_orders.append(order_data)
        else:
            unpaid_orders.append(order_data)

    return JsonResponse({
        "revenue": revenue,
        "paid_orders": paid_orders,
        "unpaid_orders": unpaid_orders,
    })
