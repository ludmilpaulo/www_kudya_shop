from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RideViewSet, driver_available_rides

router = DefaultRouter()
router.register(r'', RideViewSet, basename='ride')

urlpatterns = [
    path('driver/available/', driver_available_rides, name='rides-driver-available'),
    path('', include(router.urls)),
]
