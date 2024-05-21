from django.urls import path
from . import views

urlpatterns = [
    path('shop/<int:user_id>/', views.shop_report),
    path('shop/customers/<int:user_id>/', views.shop_customers, name='shop-customers'),
    path('shop/drivers/<int:user_id>/', views.shop_drivers, name='shop-drivers'),
    # Other URL patterns...
]