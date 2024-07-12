from rest_framework import serializers

from curtomers.models import Customer
from drivers.models import Driver
from order.models import Order, OrderDetails
from restaurants.models import Meal, Restaurant


class OrderCustomerSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Customer
        fields = ("id", "name", "avatar", "phone", "address", "location")


class OrderDriverSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Driver
        fields = ("id", "name", "avatar", "phone", "address", "location")


class OrderRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ("id", "name", "phone", "address", "location", "logo")


class OrderMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ("id", "name", "price")


class OrderDetailsSerializer(serializers.ModelSerializer):
    meal = OrderMealSerializer()

    class Meta:
        model = OrderDetails
        fields = ("id", "meal", "quantity", "sub_total")


class OrderSerializer(serializers.ModelSerializer):
    customer = OrderCustomerSerializer()
    driver = OrderDriverSerializer()
    restaurant = OrderRestaurantSerializer()
    order_details = OrderDetailsSerializer(many=True)
    status = serializers.ReadOnlyField(source="get_status_display")
    created_at = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True
    )
    picked_at = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True
    )
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "customer",
            "restaurant",
            "driver",
            "order_details",
            "total",
            "status",
            "address",
            "invoice_pdf",
            "created_at",
            "secret_pin",
            "picked_at",
            "updated_at",
        )
