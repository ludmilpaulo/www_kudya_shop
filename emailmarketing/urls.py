from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .track_views import open_tracking_pixel
from .views import EmailCampaignViewSet

router = DefaultRouter()
router.register(r'campaigns', EmailCampaignViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('email/open-tracking/<int:campaign_id>/<str:recipient>/', open_tracking_pixel, name='open_tracking'),
]
