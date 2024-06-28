from django.urls import path
from . import views

urlpatterns = [
    path('restaurant/<int:user_id>/', views.restaurant_report),
    path('restaurant/customers/<int:user_id>/', views.restaurant_customers, name='restaurant-customers'),
    path('restaurant/drivers/<int:user_id>/', views.restaurant_drivers, name='restaurant-drivers'),
    # Other URL patterns...
]
