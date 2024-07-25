from django.urls import path

from report.driver_view import driver_commission_revenue
from . import views
from . import restaurant_view


urlpatterns = [
    path("restaurant/<int:user_id>/", restaurant_view.restaurant_report),
    path(
        "restaurant/customers/<int:user_id>/",
        views.restaurant_customers,
        name="restaurant-customers",
    ),
    path(
        "restaurant/drivers/<int:user_id>/",
        views.restaurant_drivers,
        name="restaurant-drivers",
    ),
    path('driver-commission-revenue/', driver_commission_revenue, name='driver-commission-revenue'),
    # Other URL patterns...
]
