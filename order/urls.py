from django.urls import path

from order.admin_order import (
    get_orders,
    mark_as_paid,
    upload_proof_of_payment_driver,
    upload_proof_of_payment_store,
)
from order.multiple_orders import customer_add_multiple_orders
from order.order_view import check_user_coupon, customer_add_order
from .views import generate_store_invoices, store_details

urlpatterns = [
    path("orders/add/", customer_add_order, name="customer_add_order"),
    path("orders/add-multiple/", customer_add_multiple_orders),
    path(
        "store/stores/<int:store_id>/",
        store_details,
        name="store_details",
    ),
    path(
        "stores/generate_invoices/",
        generate_store_invoices,
        name="generate_invoices",
    ),
    path("api/orders/", get_orders, name="get_orders"),
    path(
        "api/upload_proof_of_payment/store/<int:order_id>/",
        upload_proof_of_payment_store,
        name="upload_proof_of_payment_store",
    ),
    path(
        "api/upload_proof_of_payment/driver/<int:order_id>/",
        upload_proof_of_payment_driver,
        name="upload_proof_of_payment_driver",
    ),
    path(
        "api/mark_as_paid/<str:type>/<int:order_id>/", mark_as_paid, name="mark_as_paid"
    ),
    path('coupons/check/', check_user_coupon, name='check_user_coupon'),
]
