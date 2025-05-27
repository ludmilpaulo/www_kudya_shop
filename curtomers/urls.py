from django.urls import path

from curtomers.views import (
    CustomerSignupView,
    customer_add_order,
    customer_driver_location,
    customer_get_detais,
    customer_get_latest_order,
    customer_get_products,
    customer_get_order_history,
    customer_get_stores,
    customer_update_profile,
    update_profile,
)


urlpatterns = [
    path("customer/products/<int:store_id>/", customer_get_products),
    path("customer/order/add/", customer_add_order),
    path("customer/stores/", customer_get_stores),
    path("signup/", CustomerSignupView.as_view()),
    path("customer/order/latest/", customer_get_latest_order),
    path("customer/driver/location/", customer_driver_location),
    path("customer/order/history/", customer_get_order_history),
    path("customer/profile/update/", customer_update_profile),
    path("customer/profile/", customer_get_detais),
    path("profile/update/", update_profile, name="update_profile"),
]
