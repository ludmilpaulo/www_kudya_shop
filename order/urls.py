from django.urls import path
from .views import customer_add_order, generate_invoices

urlpatterns = [
    path('orders/add/', customer_add_order, name='customer_add_order'),
    path('restaurants/generate_invoices/', generate_invoices, name='generate_invoices'),
]
