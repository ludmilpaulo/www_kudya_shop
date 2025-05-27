from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import storeViewSet, PartnerViewSet, DriverViewSet

router = DefaultRouter()
router.register(r"stores", storeViewSet)
router.register(r"partners", PartnerViewSet)
router.register(r"drivers", DriverViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
