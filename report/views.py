from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime, timedelta
from curtomers.models import Customer
from curtomers.serializers import CustomerSerializer
from drivers.models import Driver
from drivers.serializers import DriverSerializer
from order.models import Order
from django.db.models import Count, Sum, Case, When

from stores.models import product


User = get_user_model()






@api_view(["GET"])
def store_customers(request, user_id):
    user = User.objects.get(id=user_id)
    store = (
        user.store
    )  # Assuming user has a foreign key relationship with store model
    customers = Customer.objects.annotate(
        total_order=Count(Case(When(order__store=store, then=1)))
    ).order_by("-total_order")

    all_customers = [customer for customer in customers if customer.total_order > 0]

    serializer = CustomerSerializer(all_customers, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def store_drivers(request, user_id):
    user = User.objects.get(id=user_id)
    store = user.store
    drivers = Driver.objects.annotate(
        total_order=Count(Case(When(order__store=store, then=1)))
    ).order_by("-total_order")

    all_drivers = [driver for driver in drivers if driver.total_order > 0]

    serializer = DriverSerializer(all_drivers, many=True)
    return Response(serializer.data)
