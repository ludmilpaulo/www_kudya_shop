from django.urls import path
from django.contrib.auth import views as auth_views

from drivers.views import (
    DriverSignupView,
    driver_complete_order,
    driver_get_detais,
    driver_get_latest_order,
    driver_get_order_history,
    driver_get_profile,
    driver_get_ready_orders,
    driver_get_revenue,
    driver_pick_order,
    driver_update_location,
    driver_update_profile,
    get_ongoing_order,
    reject_order,
    test_reject_order_view,
)


urlpatterns = [
    path("signup/driver/", DriverSignupView.as_view()),
    path("orders/ready/", driver_get_ready_orders),
    path("order/pick/", driver_pick_order),
    path("order/latest/", driver_get_latest_order),
    path("order/complete/", driver_complete_order),
    path("revenue/", driver_get_revenue),
    path("location/update/", driver_update_location),
    path("profile/update/", driver_update_profile),
    path("profile/view/", driver_get_profile),
    path("order/history/", driver_get_order_history),
    path("profile/", driver_get_detais),
    path(
        "test-reject-order/<int:driver_id>/",
        test_reject_order_view,
        name="test_reject_order",
    ),
    path('reject-order/', reject_order, name='reject_order'),
    path("ongoing-order/", get_ongoing_order),
]

