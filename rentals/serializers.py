from rest_framework import serializers
from .models import RentalVehicle, RentalVehicleImage, RentalBooking


class RentalVehicleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalVehicleImage
        fields = ['id', 'image', 'order']


class RentalVehicleSerializer(serializers.ModelSerializer):
    images = RentalVehicleImageSerializer(many=True, read_only=True)

    class Meta:
        model = RentalVehicle
        fields = [
            'id', 'make', 'model', 'year', 'plate_number', 'color', 'seats',
            'transmission', 'fuel_type', 'city', 'country', 'daily_price',
            'weekly_price', 'monthly_price', 'deposit_amount', 'currency',
            'status', 'images',
        ]


class RentalBookingSerializer(serializers.ModelSerializer):
    vehicle_details = RentalVehicleSerializer(source='vehicle', read_only=True)

    class Meta:
        model = RentalBooking
        fields = [
            'id', 'booking_number', 'vehicle', 'vehicle_details', 'start_date', 'end_date',
            'pickup_location', 'return_location', 'deposit_amount', 'total_amount',
            'currency', 'status', 'payment_status', 'created_at',
        ]
        read_only_fields = ['booking_number', 'customer', 'total_amount', 'status', 'created_at']

    def create(self, validated_data):
        vehicle = validated_data['vehicle']
        days = (validated_data['end_date'] - validated_data['start_date']).days
        if days < 1:
            days = 1
        validated_data['customer'] = self.context['request'].user
        validated_data['deposit_amount'] = vehicle.deposit_amount
        validated_data['total_amount'] = vehicle.daily_price * days
        validated_data['currency'] = vehicle.currency
        return super().create(validated_data)
