"""Channel layer helpers for live ride and driver updates."""


def _get_channel_layer():
    try:
        from channels.layers import get_channel_layer
        return get_channel_layer()
    except Exception:
        return None


def broadcast_ride(ride_id: int, payload: dict) -> None:
    layer = _get_channel_layer()
    if not layer:
        return
    from asgiref.sync import async_to_sync
    async_to_sync(layer.group_send)(
        f'ride_{ride_id}',
        {'type': 'ride_update', 'data': payload},
    )


def broadcast_driver(driver_id: int, payload: dict) -> None:
    layer = _get_channel_layer()
    if not layer:
        return
    from asgiref.sync import async_to_sync
    async_to_sync(layer.group_send)(
        f'driver_{driver_id}',
        {'type': 'driver_location', 'data': payload},
    )
