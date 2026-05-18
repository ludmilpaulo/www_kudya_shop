from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccommodationListingViewSet, AccommodationBookingViewSet

router = DefaultRouter()
router.register(r'listings', AccommodationListingViewSet, basename='accommodation-listing')
router.register(r'bookings', AccommodationBookingViewSet, basename='accommodation-booking')

urlpatterns = [
    path('', include(router.urls)),
]
