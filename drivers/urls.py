from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from drivers.revenue_views import driver_get_revenue
from drivers.views import (
    DriverSignupView,
    driver_complete_order,
    driver_get_detais,
    driver_get_latest_order,
    driver_get_order_history,
    driver_get_profile,
    driver_get_ready_orders,
    driver_pick_order,
    driver_update_location,
    driver_update_profile,
    get_ongoing_order,
    get_verified_order,
    reject_order,
    test_reject_order_view,
    verify_order,
)
from drivers.delivery_views import (
    DriverViewSet,
    DeliveryRequestViewSet,
    DriverRatingViewSet,
    auto_assign_driver,
    delivery_stats
)

# REST API Router
router = DefaultRouter()
router.register(r'api/drivers', DriverViewSet, basename='api-driver')
router.register(r'api/deliveries', DeliveryRequestViewSet, basename='api-delivery')
router.register(r'api/ratings', DriverRatingViewSet, basename='api-rating')

urlpatterns = [
    # Legacy endpoints
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
    path("verify-order/", verify_order, name="verify-order"),
    path('verified-order/', get_verified_order, name='get_verified_order'),
    
    # New REST API endpoints
    path('', include(router.urls)),
    path('api/auto-assign/', auto_assign_driver, name='auto-assign-driver'),
    path('api/stats/', delivery_stats, name='delivery-stats'),
]


