from django.urls import path

from order.order_view import customer_add_order
from .views import generate_restaurant_invoices, restaurant_details

urlpatterns = [
    path('orders/add/', customer_add_order, name='customer_add_order'),
    path('restaurant/restaurants/<int:restaurant_id>/', restaurant_details, name='restaurant_details'),
    path('restaurants/generate_invoices/', generate_restaurant_invoices, name='generate_invoices'),
]
