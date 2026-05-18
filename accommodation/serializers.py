from rest_framework import serializers
from .models import AccommodationListing, AccommodationImage, AccommodationBooking


class AccommodationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationImage
        fields = ['id', 'image', 'order']


class AccommodationListingSerializer(serializers.ModelSerializer):
    images = AccommodationImageSerializer(many=True, read_only=True)
    host_name = serializers.SerializerMethodField()
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)
    country_name = serializers.CharField(source='country.name', read_only=True)

    class Meta:
        model = AccommodationListing
        fields = [
            'id', 'title', 'property_type', 'description', 'country', 'country_name',
            'city', 'city_name', 'price_per_night', 'weekly_price', 'monthly_price',
            'cleaning_fee', 'deposit', 'currency', 'max_guests', 'bedrooms',
            'bathrooms', 'beds', 'amenities', 'rules', 'check_in_time', 'check_out_time',
            'rating', 'review_count', 'images', 'host_name',
        ]

    def get_host_name(self, obj):
        return obj.host.get_full_name() or obj.host.username


class AccommodationListingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationListing
        exclude = ['host', 'approval_status', 'rating', 'review_count', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['host'] = self.context['request'].user
        return super().create(validated_data)


class AccommodationBookingSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source='listing.title', read_only=True)

    class Meta:
        model = AccommodationBooking
        fields = [
            'id', 'listing', 'listing_title', 'check_in', 'check_out', 'guests',
            'total_amount', 'currency', 'payment_status', 'booking_status',
            'special_requests', 'created_at',
        ]
        read_only_fields = ['total_amount', 'currency', 'payment_status', 'booking_status']

    def create(self, validated_data):
        listing = validated_data['listing']
        check_in = validated_data['check_in']
        check_out = validated_data['check_out']
        nights = (check_out - check_in).days
        if nights < 1:
            nights = 1
        validated_data['customer'] = self.context['request'].user
        validated_data['total_amount'] = listing.price_per_night * nights + listing.cleaning_fee
        validated_data['currency'] = listing.currency
        return super().create(validated_data)
