from django.urls import path

from report.driver_view import driver_commission_revenue
from . import views
from . import store_view


urlpatterns = [
    path("store/<int:user_id>/", store_view.store_report),
    path(
        "store/customers/<int:user_id>/",
        views.store_customers,
        name="store-customers",
    ),
    path(
        "store/drivers/<int:user_id>/",
        views.store_drivers,
        name="store-drivers",
    ),
    path('driver-commission-revenue/', driver_commission_revenue, name='driver-commission-revenue'),
    # Other URL patterns...
]
