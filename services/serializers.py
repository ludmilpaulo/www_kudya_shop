from rest_framework import serializers
from django.db.models import Sum
from .models import (
    Country, Province, ServiceCategory, Service, ServiceAvailability,
    BlackoutDate, Booking, ServiceReview, ParceirKYC, PayoutRequest,
    ParceiroEarnings
)
from stores.models import Store
from customers.models import Customer


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class ProvinceSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = Province
        fields = '__all__'


class ServiceCategorySerializer(serializers.ModelSerializer):
    service_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = '__all__'
    
    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()


class ServiceAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceAvailability
        fields = '__all__'


class BlackoutDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackoutDate
        fields = '__all__'


class ServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for service listings"""
    parceiro_name = serializers.CharField(source='parceiro.name', read_only=True)
    parceiro_logo = serializers.ImageField(source='parceiro.logo', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_bookings = serializers.IntegerField(read_only=True)
    is_verified = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'title_pt', 'description', 'description_pt',
            'price', 'currency', 'duration_minutes', 'delivery_type',
            'image', 'parceiro_name', 'parceiro_logo', 'category_name',
            'average_rating', 'total_bookings', 'is_active', 'is_featured',
            'instant_booking', 'is_verified'
        ]
    
    def get_is_verified(self, obj):
        try:
            return obj.parceiro.kyc.is_verified if hasattr(obj.parceiro, 'kyc') else False
        except:
            return False


class ServiceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single service view"""
    parceiro_name = serializers.CharField(source='parceiro.name', read_only=True)
    parceiro_logo = serializers.ImageField(source='parceiro.logo', read_only=True)
    parceiro_phone = serializers.CharField(source='parceiro.phone', read_only=True)
    parceiro_address = serializers.CharField(source='parceiro.address', read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    availability_slots = ServiceAvailabilitySerializer(many=True, read_only=True)
    blackout_dates = BlackoutDateSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_bookings = serializers.IntegerField(read_only=True)
    reviews = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    allowed_countries = CountrySerializer(many=True, read_only=True)
    allowed_provinces = ProvinceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = '__all__'
    
    def get_reviews(self, obj):
        reviews = obj.service_reviews.all()[:5]  # Latest 5 reviews
        return ServiceReviewSerializer(reviews, many=True).data
    
    def get_is_verified(self, obj):
        try:
            return obj.parceiro.kyc.is_verified if hasattr(obj.parceiro, 'kyc') else False
        except:
            return False


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating services"""
    class Meta:
        model = Service
        exclude = ['created_at', 'updated_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings"""
    class Meta:
        model = Booking
        fields = [
            'service', 'customer', 'booking_date', 'booking_time',
            'duration_minutes', 'customer_location', 'customer_latitude',
            'customer_longitude', 'customer_notes', 'payment_method'
        ]
    
    def validate(self, data):
        """Validate booking doesn't conflict with existing bookings"""
        service = data.get('service')
        booking_date = data.get('booking_date')
        booking_time = data.get('booking_time')
        
        # Create temporary booking instance to check conflicts
        temp_booking = Booking(
            service=service,
            booking_date=booking_date,
            booking_time=booking_time,
            duration_minutes=data.get('duration_minutes', service.duration_minutes)
        )
        
        if temp_booking.check_time_conflict():
            raise serializers.ValidationError("This time slot is already booked. Please choose another time.")
        
        # Set price from service if not provided
        data['price'] = service.price
        data['duration_minutes'] = data.get('duration_minutes', service.duration_minutes)
        
        return data


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for booking list and detail views"""
    service_title = serializers.CharField(source='service.title', read_only=True)
    service_image = serializers.ImageField(source='service.image', read_only=True)
    parceiro_name = serializers.CharField(source='service.parceiro.name', read_only=True)
    parceiro_phone = serializers.CharField(source='service.parceiro.phone', read_only=True)
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'


class ServiceReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceReview
        fields = '__all__'
    
    def get_customer_avatar(self, obj):
        # Return customer avatar if available
        return None  # Implement based on your customer model


class ParceirKYCSerializer(serializers.ModelSerializer):
    parceiro_name = serializers.CharField(source='parceiro.name', read_only=True)
    nationality_name = serializers.CharField(source='nationality.name', read_only=True)
    
    class Meta:
        model = ParceirKYC
        fields = '__all__'
        read_only_fields = ['status', 'is_verified', 'verified_at', 'verified_by', 'submitted_at', 'updated_at']


class PayoutRequestSerializer(serializers.ModelSerializer):
    parceiro_name = serializers.CharField(source='parceiro.name', read_only=True)
    available_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = PayoutRequest
        fields = '__all__'
        read_only_fields = ['requested_at', 'processed_at', 'completed_at', 'processed_by']
    
    def get_available_balance(self, obj):
        """Get parceiro's available balance for payout"""
        unpaid_earnings = ParceiroEarnings.objects.filter(
            parceiro=obj.parceiro,
            is_paid_out=False
        ).aggregate(total=Sum('net_amount'))
        return unpaid_earnings['total'] or 0


class ParceiroEarningsSerializer(serializers.ModelSerializer):
    parceiro_name = serializers.CharField(source='parceiro.name', read_only=True)
    
    class Meta:
        model = ParceiroEarnings
        fields = '__all__'
        read_only_fields = ['earned_at', 'paid_out_at']


class BookingStatsSerializer(serializers.Serializer):
    """Serializer for booking statistics"""
    total_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    completed_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    platform_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)


class ServiceStatsSerializer(serializers.Serializer):
    """Serializer for service statistics"""
    total_services = serializers.IntegerField()
    active_services = serializers.IntegerField()
    total_bookings = serializers.IntegerField()
    average_rating = serializers.FloatField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)

