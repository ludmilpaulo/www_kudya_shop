from rest_framework import serializers
from .models import Property, PropertyImage


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'order']


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    image_urls = serializers.SerializerMethodField()
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'address', 'city',
            'latitude', 'longitude', 'listing_type', 'listing_type_display',
            'property_type', 'property_type_display', 'price', 'currency',
            'bedrooms', 'bathrooms', 'area_sqm', 'amenities',
            'is_available', 'images', 'image_urls',
            'created_at', 'updated_at',
        ]

    def get_image_urls(self, obj):
        return [img.image.url for img in obj.images.all().order_by('order')]


class PropertyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'address', 'city',
            'latitude', 'longitude', 'listing_type', 'property_type',
            'price', 'currency', 'bedrooms', 'bathrooms', 'area_sqm',
            'amenities',
        ]
