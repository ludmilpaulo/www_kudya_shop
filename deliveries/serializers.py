import random
from rest_framework import serializers
from .models import PackageDelivery


class PackageDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageDelivery
        fields = '__all__'
        read_only_fields = [
            'delivery_number', 'customer', 'courier', 'status',
            'price', 'currency', 'distance_km', 'pickup_otp', 'delivery_otp',
            'created_at', 'completed_at',
        ]


class PackageEstimateSerializer(serializers.Serializer):
    pickup_lat = serializers.DecimalField(max_digits=10, decimal_places=7)
    pickup_lng = serializers.DecimalField(max_digits=10, decimal_places=7)
    dropoff_lat = serializers.DecimalField(max_digits=10, decimal_places=7)
    dropoff_lng = serializers.DecimalField(max_digits=10, decimal_places=7)
    package_type = serializers.ChoiceField(choices=PackageDelivery.PACKAGE_TYPES, default='small')
    urgency = serializers.ChoiceField(choices=PackageDelivery.URGENCY_CHOICES, default='standard')


class PackageRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageDelivery
        fields = [
            'package_type', 'urgency', 'pickup_address', 'pickup_lat', 'pickup_lng',
            'dropoff_address', 'dropoff_lat', 'dropoff_lng',
            'recipient_name', 'recipient_phone', 'package_notes', 'package_photo',
        ]

    def create(self, validated_data):
        from rides.pricing import haversine_km
        request = self.context['request']
        validated_data.setdefault('package_type', 'small')
        validated_data.setdefault('urgency', 'standard')
        dist = haversine_km(
            float(validated_data['pickup_lat']), float(validated_data['pickup_lng']),
            float(validated_data['dropoff_lat']), float(validated_data['dropoff_lng']),
        )
        base = {'envelope': 40, 'small': 60, 'medium': 90, 'large': 130, 'fragile': 150, 'document': 45}
        urgency_mult = {'standard': 1, 'express': 1.5, 'same_day': 2}
        price = base.get(validated_data['package_type'], 60) + float(dist) * 12
        price *= urgency_mult.get(validated_data['urgency'], 1)
        validated_data['customer'] = request.user
        validated_data['distance_km'] = dist
        validated_data['price'] = round(price, 2)
        validated_data['status'] = 'searching'
        validated_data['pickup_otp'] = f'{random.randint(100000, 999999)}'
        validated_data['delivery_otp'] = f'{random.randint(100000, 999999)}'
        return super().create(validated_data)
