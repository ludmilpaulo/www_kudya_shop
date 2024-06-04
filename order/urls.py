from django.urls import path
from .views import customer_add_order, generate_invoices, restaurant_details

urlpatterns = [
    path('orders/add/', customer_add_order, name='customer_add_order'),
    path('restaurant/restaurants/<int:restaurant_id>/', restaurant_details, name='restaurant_details'),
    path('restaurants/generate_invoices/', generate_invoices, name='generate_invoices'),
]
