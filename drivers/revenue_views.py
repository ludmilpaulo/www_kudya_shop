from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from drivers.models import Driver
from order.models import Order


@api_view(["POST"])
def driver_get_revenue(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    driver = Driver.objects.get(user=access)

    filter_type = data.get("filter_type", "week")  # default to week
    custom_start_date = data.get("start_date")
    custom_end_date = data.get("end_date")

    revenue = {}

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

    if filter_type == "day":
        for hour in range(24):
            hour_start = start_date + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            hour_orders = orders.filter(created_at__gte=hour_start, created_at__lt=hour_end)
            revenue[hour_start.strftime("%H:%M")] = sum(order.total for order in hour_orders)
    elif filter_type == "week":
        for day in range(7):
            day_date = start_date + timedelta(days=day)
            day_orders = orders.filter(
                created_at__year=day_date.year,
                created_at__month=day_date.month,
                created_at__day=day_date.day,
            )
            revenue[day_date.strftime("%a")] = sum(order.total for order in day_orders)
    elif filter_type == "month":
        for day in range((end_date - start_date).days):
            day_date = start_date + timedelta(days=day)
            day_orders = orders.filter(
                created_at__year=day_date.year,
                created_at__month=day_date.month,
                created_at__day=day_date.day,
            )
            revenue[day_date.strftime("%d/%m")] = sum(order.total for order in day_orders)
    elif filter_type == "custom":
        for day in range((end_date - start_date).days):
            day_date = start_date + timedelta(days=day)
            day_orders = orders.filter(
                created_at__year=day_date.year,
                created_at__month=day_date.month,
                created_at__day=day_date.day,
            )
            revenue[day_date.strftime("%Y-%m-%d")] = sum(order.total for order in day_orders)

    return JsonResponse({"revenue": revenue})
