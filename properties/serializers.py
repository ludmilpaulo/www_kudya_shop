from rest_framework import serializers
from .models import Property, PropertyImage, PropertyEnquiry


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'order']


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'address', 'city', 'suburb',
            'listing_type', 'property_type', 'price', 'currency',
            'monthly_rent', 'deposit', 'bedrooms', 'bathrooms',
            'area_sqm', 'land_size_sqm', 'building_size_sqm',
            'furnished', 'parking', 'pet_policy', 'available_date',
            'lease_term', 'amenities', 'images', 'owner_name',
            'latitude', 'longitude',
        ]

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username


class PropertyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        exclude = ['owner', 'is_approved', 'approval_status', 'created_at', 'updated_at']


class PropertyEnquirySerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property_listing.title', read_only=True)

    class Meta:
        model = PropertyEnquiry
        fields = [
            'id', 'property_listing', 'property_title', 'enquiry_type',
            'message', 'status', 'created_at',
        ]
        read_only_fields = ['status', 'created_at']

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)
