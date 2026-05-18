from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/rides/(?P<ride_id>\d+)/$', consumers.RideTrackingConsumer.as_asgi()),
    re_path(r'ws/drivers/(?P<driver_id>\d+)/$', consumers.DriverLocationConsumer.as_asgi()),
]
