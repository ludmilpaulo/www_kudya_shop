from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Driver, DriverLocation, DeliveryRequest, DriverRating
from .serializers import (
    DriverSerializer, DriverLocationSerializer, DeliveryRequestSerializer,
    DriverRatingSerializer, DriverStatsSerializer
)
import logging

logger = logging.getLogger(__name__)


class DriverViewSet(viewsets.ModelViewSet):
    """ViewSet for driver management"""
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_online', 'is_available', 'is_verified', 'vehicle_type']
    
    def get_queryset(self):
        user = self.request.user
        
        # If driver, return only their profile
        if hasattr(user, 'driver'):
            return self.queryset.filter(user=user)
        
        # If admin, return all
        if user.is_staff:
            return self.queryset.all()
        
        # For customers, return only verified and available drivers
        return self.queryset.filter(is_verified=True, is_available=True)
    
    @action(detail=True, methods=['post'])
    def toggle_online(self, request, pk=None):
        """Toggle driver online status"""
        driver = self.get_object()
        
        if driver.user != request.user:
            return Response(
                {'error': 'You can only toggle your own status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        driver.is_online = not driver.is_online
        driver.save()
        
        return Response({
            'status': 'online' if driver.is_online else 'offline',
            'is_online': driver.is_online
        })
    
    @action(detail=True, methods=['post'])
    def toggle_available(self, request, pk=None):
        """Toggle driver availability"""
        driver = self.get_object()
        
        if driver.user != request.user:
            return Response(
                {'error': 'You can only toggle your own availability'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        driver.is_available = not driver.is_available
        driver.save()
        
        return Response({
            'is_available': driver.is_available
        })
    
    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        """Update driver's current location"""
        driver = self.get_object()
        
        if driver.user != request.user:
            return Response(
                {'error': 'You can only update your own location'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        accuracy = request.data.get('accuracy')
        speed = request.data.get('speed')
        heading = request.data.get('heading')
        
        if not latitude or not longitude:
            return Response(
                {'error': 'Latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update driver's current location
        driver.update_location(latitude, longitude)
        
        # Create location history entry
        location = DriverLocation.objects.create(
            driver=driver,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            heading=heading
        )
        
        # If driver has active delivery, associate location with it
        active_delivery = driver.delivery_requests.filter(
            status__in=['accepted', 'picked_up', 'in_transit']
        ).first()
        
        if active_delivery:
            location.delivery_request = active_delivery
            location.save()
        
        return Response({
            'status': 'location updated',
            'latitude': latitude,
            'longitude': longitude
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get driver statistics"""
        driver = self.get_object()
        
        # Calculate earnings
        today_earnings = driver.calculate_earnings('today')
        week_earnings = driver.calculate_earnings('week')
        month_earnings = driver.calculate_earnings('month')
        total_earnings = driver.calculate_earnings('all')
        
        # Get delivery stats
        total_deliveries = driver.delivery_requests.count()
        completed_deliveries = driver.delivery_requests.filter(status='delivered').count()
        in_progress = driver.delivery_requests.filter(
            status__in=['accepted', 'picked_up', 'in_transit']
        ).count()
        
        stats = {
            'total_deliveries': total_deliveries,
            'completed_deliveries': completed_deliveries,
            'in_progress_deliveries': in_progress,
            'rejected_orders': driver.rejected_orders,
            'average_rating': float(driver.average_rating),
            'earnings': {
                'today': float(today_earnings),
                'week': float(week_earnings),
                'month': float(month_earnings),
                'total': float(total_earnings)
            }
        }
        
        serializer = DriverStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find nearby available drivers"""
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius_km = request.query_params.get('radius', 10)
        
        if not latitude or not longitude:
            return Response(
                {'error': 'Latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This is a simplified version - in production, use PostGIS for proper geo queries
        nearby_drivers = Driver.objects.filter(
            is_online=True,
            is_available=True,
            is_verified=True,
            current_latitude__isnull=False,
            current_longitude__isnull=False
        )
        
        # TODO: Implement proper distance calculation with PostGIS
        # For now, return all available drivers
        
        serializer = self.get_serializer(nearby_drivers, many=True)
        return Response(serializer.data)


class DeliveryRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for delivery requests"""
    queryset = DeliveryRequest.objects.all()
    serializer_class = DeliveryRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'request_type', 'driver']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # If driver, return their deliveries
        if hasattr(user, 'driver'):
            return self.queryset.filter(driver=user.driver)
        
        # If customer, return their order deliveries
        if hasattr(user, 'customer'):
            return self.queryset.filter(
                Q(order__customer=user.customer) |
                Q(service_booking__customer=user.customer)
            )
        
        # If store, return their deliveries
        if hasattr(user, 'store'):
            return self.queryset.filter(
                Q(order__store=user.store) |
                Q(service_booking__service__parceiro=user.store)
            )
        
        # Admin gets all
        if user.is_staff:
            return self.queryset.all()
        
        return self.queryset.none()
    
    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        """Assign delivery to a driver"""
        delivery = self.get_object()
        driver_id = request.data.get('driver_id')
        
        if not driver_id:
            return Response(
                {'error': 'Driver ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            driver = Driver.objects.get(id=driver_id, is_verified=True)
            delivery.assign_to_driver(driver)
            return Response({
                'status': 'driver assigned',
                'driver': DriverSerializer(driver).data
            })
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver not found or not verified'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Driver accepts delivery"""
        delivery = self.get_object()
        
        if not hasattr(request.user, 'driver'):
            return Response(
                {'error': 'Only drivers can accept deliveries'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if delivery.driver != request.user.driver:
            return Response(
                {'error': 'This delivery is not assigned to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        delivery.accept_by_driver()
        return Response({'status': 'delivery accepted'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Driver rejects delivery"""
        delivery = self.get_object()
        reason = request.data.get('reason', '')
        
        if not hasattr(request.user, 'driver'):
            return Response(
                {'error': 'Only drivers can reject deliveries'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if delivery.driver != request.user.driver:
            return Response(
                {'error': 'This delivery is not assigned to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        delivery.reject_by_driver(reason)
        return Response({'status': 'delivery rejected'})
    
    @action(detail=True, methods=['post'])
    def mark_picked_up(self, request, pk=None):
        """Mark delivery as picked up"""
        delivery = self.get_object()
        
        if not hasattr(request.user, 'driver'):
            return Response(
                {'error': 'Only drivers can mark as picked up'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if delivery.driver != request.user.driver:
            return Response(
                {'error': 'This delivery is not assigned to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        delivery.mark_picked_up()
        return Response({'status': 'marked as picked up'})
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark delivery as delivered"""
        delivery = self.get_object()
        
        if not hasattr(request.user, 'driver'):
            return Response(
                {'error': 'Only drivers can mark as delivered'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if delivery.driver != request.user.driver:
            return Response(
                {'error': 'This delivery is not assigned to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle proof of delivery uploads
        proof_photo = request.FILES.get('proof_photo')
        signature = request.FILES.get('signature')
        
        delivery.mark_delivered(proof_photo, signature)
        return Response({'status': 'delivery completed'})
    
    @action(detail=True, methods=['get'])
    def track(self, request, pk=None):
        """Get delivery tracking information"""
        delivery = self.get_object()
        
        # Get latest location updates
        recent_locations = delivery.location_updates.all()[:20]
        
        data = {
            'delivery': DeliveryRequestSerializer(delivery).data,
            'driver_location': None,
            'location_history': DriverLocationSerializer(recent_locations, many=True).data
        }
        
        # Add current driver location if available
        if delivery.driver and delivery.driver.current_latitude:
            data['driver_location'] = {
                'latitude': float(delivery.driver.current_latitude),
                'longitude': float(delivery.driver.current_longitude),
                'last_updated': delivery.driver.last_location_update
            }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active deliveries for driver"""
        if not hasattr(request.user, 'driver'):
            return Response(
                {'error': 'Only drivers can view active deliveries'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        active_deliveries = self.queryset.filter(
            driver=request.user.driver,
            status__in=['assigned', 'accepted', 'picked_up', 'in_transit']
        )
        
        serializer = self.get_serializer(active_deliveries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available delivery requests for driver"""
        if not hasattr(request.user, 'driver'):
            return Response(
                {'error': 'Only drivers can view available deliveries'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get pending deliveries in driver's service area
        available_deliveries = self.queryset.filter(
            status='pending'
        )
        
        # TODO: Filter by distance based on driver's current location
        
        serializer = self.get_serializer(available_deliveries, many=True)
        return Response(serializer.data)


class DriverRatingViewSet(viewsets.ModelViewSet):
    """ViewSet for driver ratings"""
    queryset = DriverRating.objects.all()
    serializer_class = DriverRatingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['driver', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # If driver, return their ratings
        if hasattr(user, 'driver'):
            return self.queryset.filter(driver=user.driver)
        
        # If customer, return ratings they've given
        if hasattr(user, 'customer'):
            return self.queryset.filter(customer=user.customer)
        
        return self.queryset.all()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_assign_driver(request):
    """Automatically assign nearest available driver to a delivery"""
    delivery_id = request.data.get('delivery_id')
    
    if not delivery_id:
        return Response(
            {'error': 'Delivery ID is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        delivery = DeliveryRequest.objects.get(id=delivery_id, status='pending')
    except DeliveryRequest.DoesNotExist:
        return Response(
            {'error': 'Delivery not found or already assigned'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Find nearest available driver
    # This is simplified - in production, use proper geospatial queries
    nearest_driver = Driver.objects.filter(
        is_online=True,
        is_available=True,
        is_verified=True
    ).first()
    
    if not nearest_driver:
        return Response(
            {'error': 'No available drivers found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    delivery.assign_to_driver(nearest_driver)
    
    return Response({
        'status': 'driver assigned',
        'delivery': DeliveryRequestSerializer(delivery).data,
        'driver': DriverSerializer(nearest_driver).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def delivery_stats(request):
    """Get delivery statistics"""
    user = request.user
    
    if hasattr(user, 'driver'):
        deliveries = DeliveryRequest.objects.filter(driver=user.driver)
    elif user.is_staff:
        deliveries = DeliveryRequest.objects.all()
    else:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    stats = {
        'total_deliveries': deliveries.count(),
        'pending': deliveries.filter(status='pending').count(),
        'assigned': deliveries.filter(status='assigned').count(),
        'in_progress': deliveries.filter(status__in=['accepted', 'picked_up', 'in_transit']).count(),
        'completed': deliveries.filter(status='delivered').count(),
        'failed': deliveries.filter(status='failed').count(),
        'total_earnings': deliveries.filter(status='delivered').aggregate(
            total=Sum('driver_commission')
        )['total'] or 0,
        'average_rating': DriverRating.objects.filter(
            driver=user.driver if hasattr(user, 'driver') else None
        ).aggregate(avg=Avg('rating'))['avg'] or 0
    }
    
    return Response(stats)

