from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from drivers.models import Driver
from contas.permissions import scope_queryset_for_user
from .models import Ride
from .serializers import RideSerializer, RideEstimateSerializer, RideRequestSerializer
from .pricing import haversine_km, estimate_duration_minutes, estimate_ride_price
from realtime.broadcast import broadcast_ride


def _ride_payload(ride):
    return RideSerializer(ride).data


class RideViewSet(viewsets.ModelViewSet):
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_platform_admin', False):
            return scope_queryset_for_user(
                user,
                Ride.objects.all().select_related('driver__user', 'customer'),
                country_lookup='country',
                city_lookup='city',
            )
        if hasattr(user, 'driver'):
            return Ride.objects.filter(
                Q(driver=user.driver) | Q(status='searching', driver__isnull=True)
            )
        return Ride.objects.filter(customer=user)

    def get_serializer_class(self):
        if self.action in ('create', 'request_ride'):
            return RideRequestSerializer
        return RideSerializer

    @action(detail=False, methods=['post'])
    def estimate(self, request):
        ser = RideEstimateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        dist = haversine_km(
            float(d['pickup_lat']), float(d['pickup_lng']),
            float(d['destination_lat']), float(d['destination_lng']),
        )
        duration = estimate_duration_minutes(dist)
        result = estimate_ride_price(
            dist, duration, d.get('ride_type', 'economy'),
            country_code=d.get('country_code', 'ZA'),
        )
        return Response(result)

    def perform_create(self, serializer):
        ride = serializer.save()
        broadcast_ride(ride.id, {'type': 'ride_status', 'ride': _ride_payload(ride)})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            RideSerializer(serializer.instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=False, methods=['post'], url_path='request')
    def request_ride(self, request):
        return self.create(request)

    @action(detail=False, methods=['get'])
    def history(self, request):
        qs = self.get_queryset().exclude(status='requested').order_by('-created_at')[:50]
        return Response(RideSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        ride = self.get_object()
        if not hasattr(request.user, 'driver'):
            return Response({'detail': 'Driver only.'}, status=status.HTTP_403_FORBIDDEN)
        driver = request.user.driver
        if not driver.is_online:
            return Response({'detail': 'Go online first.'}, status=status.HTTP_400_BAD_REQUEST)
        ride.driver = driver
        ride.status = 'accepted'
        ride.accepted_at = timezone.now()
        ride.save()
        broadcast_ride(ride.id, {'type': 'ride_status', 'ride': _ride_payload(ride)})
        return Response(RideSerializer(ride).data)

    @action(detail=True, methods=['post'])
    def arrived(self, request, pk=None):
        ride = self._driver_ride(request, pk)
        ride.status = 'arrived'
        ride.arrived_at = timezone.now()
        ride.save()
        broadcast_ride(ride.id, {'type': 'ride_status', 'ride': _ride_payload(ride)})
        return Response(RideSerializer(ride).data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        ride = self._driver_ride(request, pk)
        ride.status = 'in_progress'
        ride.started_at = timezone.now()
        ride.save()
        broadcast_ride(ride.id, {'type': 'ride_status', 'ride': _ride_payload(ride)})
        return Response(RideSerializer(ride).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        ride = self._driver_ride(request, pk)
        ride.status = 'completed'
        ride.completed_at = timezone.now()
        ride.final_price = request.data.get('final_price', ride.estimated_price)
        ride.payment_status = 'paid'
        ride.save()
        if ride.driver:
            ride.driver.completed_deliveries += 1
            ride.driver.save(update_fields=['completed_deliveries'])
        broadcast_ride(ride.id, {'type': 'ride_status', 'ride': _ride_payload(ride)})
        return Response(RideSerializer(ride).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        ride = self.get_object()
        if ride.customer != request.user and (
            not hasattr(request.user, 'driver') or ride.driver != request.user.driver
        ) and not getattr(request.user, 'is_platform_admin', False):
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        ride.status = 'cancelled'
        ride.cancelled_at = timezone.now()
        ride.cancellation_reason = request.data.get('reason', '')
        ride.save()
        broadcast_ride(ride.id, {'type': 'ride_status', 'ride': _ride_payload(ride)})
        return Response(RideSerializer(ride).data)

    def _driver_ride(self, request, pk):
        from rest_framework.exceptions import PermissionDenied
        ride = self.get_object()
        if not hasattr(request.user, 'driver') or ride.driver_id != request.user.driver.id:
            raise PermissionDenied('Not your ride')
        return ride


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_available_rides(request):
    """Rides searching for a driver near driver location."""
    if not hasattr(request.user, 'driver'):
        return Response({'detail': 'Driver only.'}, status=status.HTTP_403_FORBIDDEN)
    qs = Ride.objects.filter(status='searching', driver__isnull=True).order_by('-created_at')[:20]
    return Response(RideSerializer(qs, many=True).data)
