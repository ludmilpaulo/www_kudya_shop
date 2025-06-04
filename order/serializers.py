from rest_framework import serializers

from customers.models import Customer
from drivers.models import Driver
from order.models import Order, OrderDetails
from stores.models import product, store


class OrderCustomerSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Customer
        fields = ("id", "name", "avatar", "phone", "address", "location")


class OrderDriverSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Driver
        fields = ("id", "name", "avatar", "phone", "address", "location","plate","make")


class OrderstoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = store
        fields = ("id", "name", "phone", "address", "location", "logo")


class OrderproductSerializer(serializers.ModelSerializer):
    class Meta:
        model = product
        fields = ("id", "name", "price")


class OrderDetailsSerializer(serializers.ModelSerializer):
    product = OrderproductSerializer()

    class Meta:
        model = OrderDetails
        fields = ("id", "product", "quantity", "sub_total")


class OrderSerializer(serializers.ModelSerializer):
    customer = OrderCustomerSerializer()
    driver = OrderDriverSerializer()
    store = OrderstoreSerializer()
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
            "store",
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
            "proof_of_payment_store",
            "proof_of_payment_driver",
            "payment_status_store",
            "original_price",
            "location",
            "use_current_location",
        )
