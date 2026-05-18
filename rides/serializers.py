from rest_framework import serializers
from .models import Ride


class RideSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()
    driver_phone = serializers.SerializerMethodField()
    driver_lat = serializers.DecimalField(
        source='driver.current_latitude', max_digits=10, decimal_places=7, read_only=True, allow_null=True,
    )
    driver_lng = serializers.DecimalField(
        source='driver.current_longitude', max_digits=10, decimal_places=7, read_only=True, allow_null=True,
    )

    class Meta:
        model = Ride
        fields = [
            'id', 'ride_number', 'customer', 'driver', 'driver_name', 'driver_phone',
            'driver_lat', 'driver_lng', 'ride_type', 'status', 'pickup_address',
            'pickup_lat', 'pickup_lng', 'destination_address', 'destination_lat',
            'destination_lng', 'estimated_price', 'final_price', 'currency',
            'distance_km', 'duration_minutes', 'surge_multiplier', 'payment_status',
            'payment_method', 'scheduled_at', 'share_trip_token', 'created_at',
            'accepted_at', 'arrived_at', 'started_at', 'completed_at',
        ]
        read_only_fields = [
            'ride_number', 'status', 'driver', 'final_price', 'share_trip_token',
            'accepted_at', 'arrived_at', 'started_at', 'completed_at',
        ]

    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.user.get_full_name() or obj.driver.user.username
        return None

    def get_driver_phone(self, obj):
        return obj.driver.phone if obj.driver else None


class RideEstimateSerializer(serializers.Serializer):
    pickup_lat = serializers.DecimalField(max_digits=10, decimal_places=7)
    pickup_lng = serializers.DecimalField(max_digits=10, decimal_places=7)
    destination_lat = serializers.DecimalField(max_digits=10, decimal_places=7)
    destination_lng = serializers.DecimalField(max_digits=10, decimal_places=7)
    ride_type = serializers.ChoiceField(choices=Ride.RIDE_TYPES, default='economy')
    country_code = serializers.CharField(max_length=3, default='ZA', required=False)


class RideRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = [
            'pickup_address', 'pickup_lat', 'pickup_lng',
            'destination_address', 'destination_lat', 'destination_lng',
            'ride_type', 'payment_method', 'scheduled_at', 'country', 'city',
        ]

    def create(self, validated_data):
        from .pricing import haversine_km, estimate_duration_minutes, estimate_ride_price
        request = self.context['request']
        lat1 = float(validated_data['pickup_lat'])
        lng1 = float(validated_data['pickup_lng'])
        lat2 = float(validated_data['destination_lat'])
        lng2 = float(validated_data['destination_lng'])
        dist = haversine_km(lat1, lng1, lat2, lng2)
        duration = estimate_duration_minutes(dist)
        country_code = 'ZA'
        if validated_data.get('country'):
            country_code = validated_data['country'].code
        pricing = estimate_ride_price(
            dist, duration,
            validated_data.get('ride_type', 'economy'),
            country_code=country_code,
        )
        validated_data['customer'] = request.user
        validated_data['distance_km'] = dist
        validated_data['duration_minutes'] = duration
        validated_data['estimated_price'] = pricing['estimated_price']
        validated_data['currency'] = pricing['currency']
        validated_data['status'] = 'searching'
        return super().create(validated_data)
