from rest_framework import serializers
from .models import Driver, DriverLocation, DeliveryRequest, DriverRating
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class DriverSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    rating_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ['user', 'total_deliveries', 'completed_deliveries', 'average_rating', 'created_at', 'updated_at']
    
    def get_rating_count(self, obj):
        return obj.ratings.count()


class DriverLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverLocation
        fields = '__all__'


class DeliveryRequestSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.user.get_full_name', read_only=True)
    driver_phone = serializers.CharField(source='driver.phone', read_only=True)
    driver_vehicle = serializers.CharField(source='driver.vehicle_type', read_only=True)
    driver_plate = serializers.CharField(source='driver.plate', read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryRequest
        fields = '__all__'
        read_only_fields = ['request_number', 'created_at', 'assigned_at', 'accepted_at', 'picked_up_at', 'delivered_at']
    
    def get_customer_name(self, obj):
        if obj.order:
            return obj.order.customer.user.get_full_name()
        elif obj.service_booking:
            return obj.service_booking.customer.user.get_full_name()
        return None
    
    def get_customer_phone(self, obj):
        if obj.order:
            return obj.order.customer.phone
        elif obj.service_booking:
            return obj.service_booking.customer.phone
        return None


class DriverRatingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    driver_name = serializers.CharField(source='driver.user.get_full_name', read_only=True)
    
    class Meta:
        model = DriverRating
        fields = '__all__'
        read_only_fields = ['created_at']


class DriverStatsSerializer(serializers.Serializer):
    total_deliveries = serializers.IntegerField()
    completed_deliveries = serializers.IntegerField()
    in_progress_deliveries = serializers.IntegerField()
    rejected_orders = serializers.IntegerField()
    average_rating = serializers.FloatField()
    earnings = serializers.DictField()
