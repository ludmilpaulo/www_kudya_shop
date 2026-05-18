from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CountryViewSet, ProvinceViewSet

router = DefaultRouter()
router.register(r'provinces', ProvinceViewSet, basename='api-province')
router.register(r'', CountryViewSet, basename='api-country')

urlpatterns = [
    path('', include(router.urls)),
]
