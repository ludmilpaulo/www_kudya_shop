from django.urls import path

from order.admin_order import (
    get_orders,
    mark_as_paid,
    upload_proof_of_payment_driver,
    upload_proof_of_payment_restaurant,
)
from order.order_view import customer_add_order
from .views import generate_restaurant_invoices, restaurant_details

urlpatterns = [
    path("orders/add/", customer_add_order, name="customer_add_order"),
    path(
        "restaurant/restaurants/<int:restaurant_id>/",
        restaurant_details,
        name="restaurant_details",
    ),
    path(
        "restaurants/generate_invoices/",
        generate_restaurant_invoices,
        name="generate_invoices",
    ),
    path("api/orders/", get_orders, name="get_orders"),
    path(
        "api/upload_proof_of_payment/restaurant/<int:order_id>/",
        upload_proof_of_payment_restaurant,
        name="upload_proof_of_payment_restaurant",
    ),
    path(
        "api/upload_proof_of_payment/driver/<int:order_id>/",
        upload_proof_of_payment_driver,
        name="upload_proof_of_payment_driver",
    ),
    path(
        "api/mark_as_paid/<str:type>/<int:order_id>/", mark_as_paid, name="mark_as_paid"
    ),
]
