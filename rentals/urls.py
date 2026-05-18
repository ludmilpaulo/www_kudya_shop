from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RentalVehicleViewSet, RentalBookingViewSet

router = DefaultRouter()
router.register(r'vehicles', RentalVehicleViewSet, basename='rental-vehicle')
router.register(r'bookings', RentalBookingViewSet, basename='rental-booking')

urlpatterns = [
    path('', include(router.urls)),
]
