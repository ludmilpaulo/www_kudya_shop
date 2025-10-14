from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CountryViewSet, ProvinceViewSet, ServiceCategoryViewSet,
    ServiceViewSet, ServiceAvailabilityViewSet, BlackoutDateViewSet,
    BookingViewSet, ServiceReviewViewSet,
    ParceirKYCViewSet, PayoutRequestViewSet, ParceiroEarningsViewSet,
    service_search, booking_stats
)

router = DefaultRouter()
router.register(r'countries', CountryViewSet, basename='country')
router.register(r'provinces', ProvinceViewSet, basename='province')
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'availability', ServiceAvailabilityViewSet, basename='availability')
router.register(r'blackouts', BlackoutDateViewSet, basename='blackout')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', ServiceReviewViewSet, basename='service-review')
router.register(r'kyc', ParceirKYCViewSet, basename='kyc')
router.register(r'payouts', PayoutRequestViewSet, basename='payout')
router.register(r'earnings', ParceiroEarningsViewSet, basename='earnings')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', service_search, name='service-search'),
    path('bookings/stats/', booking_stats, name='booking-stats'),
]

