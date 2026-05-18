from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from contas.permissions import scope_queryset_for_user
from .models import AccommodationListing, AccommodationBooking
from .serializers import (
    AccommodationListingSerializer,
    AccommodationListingCreateSerializer,
    AccommodationBookingSerializer,
)


class AccommodationListingViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'country', 'city', 'max_guests']
    search_fields = ['title', 'description', 'address']
    ordering_fields = ['price_per_night', 'rating', 'created_at']
    ordering = ['-rating']

    def get_queryset(self):
        qs = AccommodationListing.objects.filter(
            approval_status='approved',
            is_active=True,
        ).select_related('host', 'country', 'city').prefetch_related('images')
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return AccommodationListing.objects.filter(host=self.request.user)
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AccommodationListingCreateSerializer
        return AccommodationListingSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save()


class AccommodationBookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AccommodationBookingSerializer
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_platform_admin', False):
            return scope_queryset_for_user(
                user,
                AccommodationBooking.objects.all(),
                country_lookup='listing__country',
                city_lookup='listing__city',
            )
        if user.accommodation_listings.exists():
            return AccommodationBooking.objects.filter(listing__host=user)
        return AccommodationBooking.objects.filter(customer=user)

    @action(detail=False, methods=['get'])
    def history(self, request):
        qs = self.get_queryset().order_by('-created_at')
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.booking_status = 'cancelled'
        booking.save(update_fields=['booking_status'])
        return Response(self.get_serializer(booking).data)
