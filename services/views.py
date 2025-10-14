from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Country, Province, ServiceCategory, Service, ServiceAvailability,
    BlackoutDate, Booking, ServiceReview, ParceirKYC, PayoutRequest,
    ParceiroEarnings
)
from .serializers import (
    CountrySerializer, ProvinceSerializer, ServiceCategorySerializer,
    ServiceListSerializer, ServiceDetailSerializer, ServiceCreateUpdateSerializer,
    ServiceAvailabilitySerializer, BlackoutDateSerializer,
    BookingSerializer, BookingCreateSerializer, ServiceReviewSerializer,
    ParceirKYCSerializer, PayoutRequestSerializer, ParceiroEarningsSerializer,
    BookingStatsSerializer, ServiceStatsSerializer
)


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for countries"""
    queryset = Country.objects.filter(is_active=True)
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]


class ProvinceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for provinces/states"""
    queryset = Province.objects.filter(is_active=True)
    serializer_class = ProvinceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['country']


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for service categories"""
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category_type', 'requires_license']
    search_fields = ['name', 'name_pt', 'description']


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for services"""
    queryset = Service.objects.filter(is_active=True).select_related('parceiro', 'category')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'delivery_type', 'is_featured', 'instant_booking', 'parceiro']
    search_fields = ['title', 'title_pt', 'description', 'description_pt', 'tags']
    ordering_fields = ['price', 'created_at', 'average_rating']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ServiceCreateUpdateSerializer
        return ServiceDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by location
        country_id = self.request.query_params.get('country')
        province_id = self.request.query_params.get('province')
        
        if country_id or province_id:
            if country_id and not queryset.filter(allowed_countries__id=country_id).exists():
                queryset = queryset.filter(allowed_countries__isnull=True)
            if province_id and not queryset.filter(allowed_provinces__id=province_id).exists():
                queryset = queryset.filter(allowed_provinces__isnull=True)
        
        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            # This would require annotation
            pass
        
        # Filter by verified parceiros
        verified_only = self.request.query_params.get('verified_only')
        if verified_only == 'true':
            queryset = queryset.filter(parceiro__kyc__is_verified=True)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get service availability for a specific date range"""
        service = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date:
            start_date = timezone.now().date()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = start_date + timedelta(days=7)
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        available_slots = self.get_available_slots(service, start_date, end_date)
        
        return Response({
            'service_id': service.id,
            'start_date': start_date,
            'end_date': end_date,
            'available_slots': available_slots
        })
    
    def get_available_slots(self, service, start_date, end_date):
        """Get available time slots for a date range"""
        slots_by_date = {}
        current_date = start_date
        
        while current_date <= end_date:
            day_of_week = current_date.isoweekday()
            
            # Check if date is in blackout period
            is_blackout = service.blackout_dates.filter(
                start_date__lte=current_date,
                end_date__gte=current_date
            ).exists()
            
            if not is_blackout:
                # Get availability for this day
                availabilities = service.availability_slots.filter(
                    Q(is_recurring=True, day_of_week=day_of_week, is_active=True) |
                    Q(is_recurring=False, specific_date=current_date, is_active=True)
                )
                
                day_slots = []
                for availability in availabilities:
                    # Generate time slots
                    time_slots = availability.generate_time_slots(current_date, service.duration_minutes)
                    
                    # Check which slots are already booked
                    for time_slot in time_slots:
                        is_booked = Booking.objects.filter(
                            service=service,
                            booking_date=current_date,
                            booking_time=time_slot,
                            status__in=['pending', 'confirmed', 'in_progress']
                        ).exists()
                        
                        if not is_booked:
                            day_slots.append({
                                'time': time_slot.strftime('%H:%M'),
                                'available': True
                            })
                
                if day_slots:
                    slots_by_date[current_date.isoformat()] = day_slots
            
            current_date += timedelta(days=1)
        
        return slots_by_date
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get service reviews"""
        service = self.get_object()
        reviews = service.service_reviews.all()
        serializer = ServiceReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured services"""
        featured_services = self.queryset.filter(is_featured=True)[:10]
        serializer = self.get_serializer(featured_services, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Get nearby services (placeholder - requires geolocation)"""
        # This would require implementing geospatial queries
        # For now, return all services
        services = self.queryset.all()[:20]
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)


class ServiceAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = ServiceAvailability.objects.all()
    serializer_class = ServiceAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service', 'is_recurring', 'day_of_week', 'specific_date']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if hasattr(user, 'store') and not user.is_staff:
            return qs.filter(service__parceiro=user.store)
        return qs


class BlackoutDateViewSet(viewsets.ModelViewSet):
    queryset = BlackoutDate.objects.all()
    serializer_class = BlackoutDateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if hasattr(user, 'store') and not user.is_staff:
            return qs.filter(service__parceiro=user.store)
        return qs

class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for bookings"""
    queryset = Booking.objects.all().select_related('service', 'customer')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'booking_date']
    ordering_fields = ['booking_date', 'booking_time', 'created_at']
    ordering = ['-booking_date', '-booking_time']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if hasattr(user, 'customer'):
            queryset = queryset.filter(customer=user.customer)
        elif hasattr(user, 'store'):
            queryset = queryset.filter(service__parceiro=user.store)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create booking and send confirmation"""
        booking = serializer.save()
        
        # If instant booking is enabled, confirm immediately
        if booking.service.instant_booking:
            booking.status = 'confirmed'
            booking.confirmed_at = timezone.now()
            booking.save()
        
        # Send confirmation email
        booking.send_confirmation_email()
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm booking (parceiro action)"""
        booking = self.get_object()
        
        if booking.status == 'pending':
            booking.status = 'confirmed'
            booking.confirmed_at = timezone.now()
            booking.save()
            return Response({'status': 'booking confirmed'})
        
        return Response(
            {'error': 'Booking cannot be confirmed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel booking"""
        booking = self.get_object()
        reason = request.data.get('reason', '')
        
        user = request.user
        if hasattr(user, 'customer') and booking.customer == user.customer:
            booking.status = 'cancelled_customer'
        elif hasattr(user, 'store') and booking.service.parceiro == user.store:
            booking.status = 'cancelled_provider'
        else:
            return Response(
                {'error': 'You do not have permission to cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.cancellation_reason = reason
        booking.save()
        
        return Response({'status': 'booking cancelled'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark booking as completed"""
        booking = self.get_object()
        
        if booking.status == 'in_progress':
            booking.status = 'completed'
            booking.completed_at = timezone.now()
            booking.save()
            
            # Create earnings record
            ParceiroEarnings.objects.create(
                parceiro=booking.service.parceiro,
                earning_type='service_booking',
                booking=booking,
                gross_amount=booking.price,
                platform_fee=booking.platform_fee,
                net_amount=booking.provider_earnings
            )
            
            return Response({'status': 'booking completed'})
        
        return Response(
            {'error': 'Booking cannot be completed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming bookings"""
        queryset = self.get_queryset().filter(
            booking_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get booking history"""
        queryset = self.get_queryset().filter(
            status__in=['completed', 'cancelled_customer', 'cancelled_provider', 'no_show']
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ServiceReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for service reviews"""
    queryset = ServiceReview.objects.all()
    serializer_class = ServiceReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['service', 'rating']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Create review for completed booking"""
        booking_id = self.request.data.get('booking_id')
        
        if booking_id:
            try:
                booking = Booking.objects.get(
                    id=booking_id,
                    customer=self.request.user.customer,
                    status='completed'
                )
                serializer.save(
                    booking=booking,
                    service=booking.service,
                    customer=self.request.user.customer
                )
            except Booking.DoesNotExist:
                pass


class ParceirKYCViewSet(viewsets.ModelViewSet):
    """ViewSet for KYC verification"""
    queryset = ParceirKYC.objects.all()
    serializer_class = ParceirKYCSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'store'):
            return self.queryset.filter(parceiro=user.store)
        elif user.is_staff:
            return self.queryset.all()
        return self.queryset.none()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve KYC (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only admins can approve KYC'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        kyc = self.get_object()
        kyc.approve(request.user)
        return Response({'status': 'KYC approved'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject KYC (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only admins can reject KYC'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        kyc = self.get_object()
        reason = request.data.get('reason', 'Not specified')
        kyc.reject(reason)
        return Response({'status': 'KYC rejected'})


class PayoutRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for payout requests"""
    queryset = PayoutRequest.objects.all()
    serializer_class = PayoutRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    ordering = ['-requested_at']
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'store'):
            return self.queryset.filter(parceiro=user.store)
        elif user.is_staff:
            return self.queryset.all()
        return self.queryset.none()
    
    @action(detail=False, methods=['get'])
    def available_balance(self, request):
        """Get available balance for payout"""
        if not hasattr(request.user, 'store'):
            return Response(
                {'error': 'Only parceiros can check balance'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        unpaid_earnings = ParceiroEarnings.objects.filter(
            parceiro=request.user.store,
            is_paid_out=False
        ).aggregate(total=Sum('net_amount'))
        
        return Response({
            'available_balance': unpaid_earnings['total'] or 0,
            'currency': 'AOA'
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_completed(self, request, pk=None):
        if not request.user.is_staff:
            return Response({'error': 'Only admins can complete payouts'}, status=status.HTTP_403_FORBIDDEN)
        payout = self.get_object()
        payout.status = 'completed'
        payout.completed_at = timezone.now()
        payout.processed_by = request.user
        payout.save()
        return Response({'status': 'completed'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_processing(self, request, pk=None):
        if not request.user.is_staff:
            return Response({'error': 'Only admins can process payouts'}, status=status.HTTP_403_FORBIDDEN)
        payout = self.get_object()
        payout.status = 'processing'
        payout.processed_at = timezone.now()
        payout.processed_by = request.user
        payout.save()
        return Response({'status': 'processing'})


class ParceiroEarningsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for parceiro earnings"""
    queryset = ParceiroEarnings.objects.all()
    serializer_class = ParceiroEarningsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['earning_type', 'is_paid_out']
    ordering = ['-earned_at']
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'store'):
            return self.queryset.filter(parceiro=user.store)
        return self.queryset.none()
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get earnings statistics"""
        if not hasattr(request.user, 'store'):
            return Response(
                {'error': 'Only parceiros can view earnings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        period = request.query_params.get('period', 'all')
        
        if period == 'today':
            queryset = queryset.filter(earned_at__date=timezone.now().date())
        elif period == 'week':
            queryset = queryset.filter(earned_at__gte=timezone.now() - timedelta(days=7))
        elif period == 'month':
            queryset = queryset.filter(earned_at__gte=timezone.now() - timedelta(days=30))
        
        stats = queryset.aggregate(
            total_earnings=Sum('net_amount'),
            total_platform_fees=Sum('platform_fee'),
            total_transactions=Count('id'),
            paid_out=Sum('net_amount', filter=Q(is_paid_out=True)),
            pending=Sum('net_amount', filter=Q(is_paid_out=False))
        )
        
        return Response(stats)


@api_view(['GET'])
@permission_classes([AllowAny])
def service_search(request):
    """Advanced service search with filters"""
    query = request.GET.get('q', '')
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    delivery_type = request.GET.get('delivery_type')
    verified_only = request.GET.get('verified_only')
    
    services = Service.objects.filter(is_active=True)
    
    if query:
        services = services.filter(
            Q(title__icontains=query) |
            Q(title_pt__icontains=query) |
            Q(description__icontains=query) |
            Q(description_pt__icontains=query) |
            Q(tags__icontains=query)
        )
    
    if category:
        services = services.filter(category_id=category)
    
    if min_price:
        services = services.filter(price__gte=min_price)
    
    if max_price:
        services = services.filter(price__lte=max_price)
    
    if delivery_type:
        services = services.filter(delivery_type=delivery_type)
    
    if verified_only == 'true':
        services = services.filter(parceiro__kyc__is_verified=True)
    
    serializer = ServiceListSerializer(services, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_stats(request):
    """Get booking statistics for parceiro or customer"""
    user = request.user
    
    if hasattr(user, 'store'):
        # Parceiro stats
        bookings = Booking.objects.filter(service__parceiro=user.store)
    elif hasattr(user, 'customer'):
        # Customer stats
        bookings = Booking.objects.filter(customer=user.customer)
    else:
        return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
    
    stats = {
        'total_bookings': bookings.count(),
        'pending_bookings': bookings.filter(status='pending').count(),
        'confirmed_bookings': bookings.filter(status='confirmed').count(),
        'completed_bookings': bookings.filter(status='completed').count(),
        'cancelled_bookings': bookings.filter(status__in=['cancelled_customer', 'cancelled_provider']).count(),
        'total_revenue': bookings.filter(status='completed').aggregate(total=Sum('price'))['total'] or 0,
        'platform_earnings': bookings.filter(status='completed').aggregate(total=Sum('platform_fee'))['total'] or 0,
    }
    
    serializer = BookingStatsSerializer(stats)
    return Response(serializer.data)
