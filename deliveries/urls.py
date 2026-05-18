from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PackageDeliveryViewSet

router = DefaultRouter()
router.register(r'', PackageDeliveryViewSet, basename='package-delivery')

urlpatterns = [
    path('', include(router.urls)),
]
