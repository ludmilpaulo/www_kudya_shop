from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import VerificationDocumentViewSet


router = DefaultRouter()
router.register(r'verification-documents', VerificationDocumentViewSet, basename='verification-document')

urlpatterns = [
    path('', include(router.urls)),
]
