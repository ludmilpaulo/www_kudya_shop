from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from contas.permissions import scope_queryset_for_user
from .models import PackageDelivery
from .serializers import PackageDeliverySerializer, PackageEstimateSerializer, PackageRequestSerializer
from rides.pricing import haversine_km


class PackageDeliveryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_platform_admin', False):
            return scope_queryset_for_user(
                user,
                PackageDelivery.objects.all(),
                country_lookup='customer__country',
                city_lookup='customer__city',
            )
        if hasattr(user, 'driver'):
            return PackageDelivery.objects.filter(
                Q(courier=user.driver) | Q(status='searching', courier__isnull=True)
            )
        return PackageDelivery.objects.filter(customer=user)

    def get_serializer_class(self):
        if self.action in ('create', 'request_delivery'):
            return PackageRequestSerializer
        return PackageDeliverySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            PackageDeliverySerializer(serializer.instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=False, methods=['post'])
    def estimate(self, request):
        ser = PackageEstimateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        dist = haversine_km(
            float(d['pickup_lat']), float(d['pickup_lng']),
            float(d['dropoff_lat']), float(d['dropoff_lng']),
        )
        base = {'envelope': 40, 'small': 60, 'medium': 90, 'large': 130, 'fragile': 150, 'document': 45}
        urgency_mult = {'standard': 1, 'express': 1.5, 'same_day': 2}
        price = base.get(d['package_type'], 60) + float(dist) * 12
        price *= urgency_mult.get(d['urgency'], 1)
        return Response({'distance_km': str(dist), 'estimated_price': str(round(price, 2)), 'currency': 'ZAR'})

    @action(detail=False, methods=['post'], url_path='request')
    def request_delivery(self, request):
        return self.create(request)

    @action(detail=False, methods=['get'])
    def history(self, request):
        qs = self.get_queryset().order_by('-created_at')[:50]
        return Response(PackageDeliverySerializer(qs, many=True).data)

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        delivery = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'status': 'Required.'}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(request.user, 'driver') and delivery.courier_id != request.user.driver.id:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        delivery.status = new_status
        if new_status == 'delivered':
            delivery.completed_at = timezone.now()
        delivery.save()
        return Response(PackageDeliverySerializer(delivery).data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        delivery = self.get_object()
        if not hasattr(request.user, 'driver'):
            return Response({'detail': 'Courier only.'}, status=status.HTTP_403_FORBIDDEN)
        delivery.courier = request.user.driver
        delivery.status = 'accepted'
        delivery.save()
        return Response(PackageDeliverySerializer(delivery).data)
