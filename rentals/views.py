from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import RentalVehicle, RentalBooking
from .serializers import RentalVehicleSerializer, RentalBookingSerializer


class RentalVehicleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RentalVehicleSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['city', 'country', 'transmission', 'fuel_type', 'seats']

    def get_queryset(self):
        qs = RentalVehicle.objects.filter(is_approved=True, status='available').prefetch_related('images')
        city = self.request.query_params.get('city')
        if city:
            qs = qs.filter(city_id=city)
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            qs = qs.filter(daily_price__gte=min_price)
        if max_price:
            qs = qs.filter(daily_price__lte=max_price)
        return qs


class RentalBookingViewSet(viewsets.ModelViewSet):
    serializer_class = RentalBookingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return RentalBooking.objects.all()
        if RentalVehicle.objects.filter(partner=user).exists():
            return RentalBooking.objects.filter(vehicle__partner=user)
        return RentalBooking.objects.filter(customer=user)

    @action(detail=False, methods=['post'], url_path='book')
    def book(self, request):
        return self.create(request)

    @action(detail=False, methods=['get'])
    def history(self, request):
        return Response(self.get_serializer(self.get_queryset().order_by('-created_at')[:50], many=True).data)

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        booking = self.get_object()
        if booking.vehicle.partner != request.user and not request.user.is_staff:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        booking.status = request.data.get('status', booking.status)
        booking.save()
        return Response(self.get_serializer(booking).data)
