from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CityViewSet,
    CountryComplianceSettingViewSet,
    AuditEventViewSet,
    translations_bundle,
    home_modules,
)

router = DefaultRouter()
router.register(r'cities', CityViewSet, basename='city')
router.register(r'compliance', CountryComplianceSettingViewSet, basename='country-compliance')
router.register(r'audit-events', AuditEventViewSet, basename='audit-event')

urlpatterns = [
    path('', include(router.urls)),
    path('translations/', translations_bundle, name='translations-bundle'),
    path('home-modules/', home_modules, name='home-modules'),
]
