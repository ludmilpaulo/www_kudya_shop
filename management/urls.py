from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, PartnerViewSet, DriverViewSet

router = DefaultRouter()
router.register(r"restaurants", RestaurantViewSet)
router.register(r"partners", PartnerViewSet)
router.register(r"drivers", DriverViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
