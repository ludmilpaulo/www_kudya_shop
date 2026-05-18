import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class RideTrackingConsumer(AsyncJsonWebsocketConsumer):
    """Customer subscribes to live ride status and driver position."""

    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.group = f'ride_{self.ride_id}'
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'ride_id': self.ride_id})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def ride_update(self, event):
        await self.send_json(event['data'])


class DriverLocationConsumer(AsyncJsonWebsocketConsumer):
    """Subscribe to a driver's live GPS (for active trip tracking)."""

    async def connect(self):
        self.driver_id = self.scope['url_route']['kwargs']['driver_id']
        self.group = f'driver_{self.driver_id}'
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def driver_location(self, event):
        await self.send_json(event['data'])
