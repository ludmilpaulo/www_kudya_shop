from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .application import JobApplicationViewSet


from .views import CareerViewSet

router = DefaultRouter()
router.register(r'careers', CareerViewSet, basename='career')
router.register(r'job-applications', JobApplicationViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
