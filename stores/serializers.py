from rest_framework import serializers
from stores.models import (
    Product,
    ProductCategory,
    OpeningHour,
    Store,
    StoreCategory,
)
from django.contrib.auth import get_user_model

from stores.models.product import Size, ProductCategory

User = get_user_model()


class OpeningHourSerializer(serializers.ModelSerializer):
    day = serializers.SerializerMethodField()

    def get_day(self, obj):
        return obj.get_day_display()

    class Meta:
        model = OpeningHour
        fields = ("day", "from_hour", "to_hour", "is_closed")


class StoreSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    logo = serializers.ImageField(required=False, allow_empty_file=True)
    store_license = serializers.FileField(required=False, allow_empty_file=True)
    opening_hours = OpeningHourSerializer(
        many=True, source="openinghour_set", required=False
    )

    def get_category(self, store):
        category = store.category
        if category:
            return {
                "id": category.id,
                "name": category.name,
                "image": self.get_category_image_url(category),
            }
        return None

    def get_category_image_url(self, category):
        request = self.context.get("request")
        if category.image:
            image_url = category.image.url
            return request.build_absolute_uri(image_url)
        return None

    def get_logo(self, store):
        request = self.context.get("request")
        logo_url = store.logo.url
        return request.build_absolute_uri(logo_url)

    def update(self, instance, validated_data):
        # Update basic fields
        instance.name = validated_data.get("name", instance.name)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.address = validated_data.get("address", instance.address)
        instance.barnner = validated_data.get("barnner", instance.barnner)
        instance.is_approved = validated_data.get("is_approved", instance.is_approved)
        instance.location = validated_data.get("location", instance.location)

        # Handle logo and license
        if "logo" in validated_data:
            instance.logo = validated_data["logo"]
        if "store_license" in validated_data:
            instance.store_license = validated_data["store_license"]

        instance.save()
        return instance

    class Meta:
        model = Store
        fields = (
            "id",
            "name",
            "phone",
            "address",
            "logo",
            "store_license",
            "category",
            "barnner",
            "is_approved",
            "opening_hours",
            "location",
        )


class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()


    class Meta:
        model = Product
        fields = "__all__"

    def get_image_url(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_sizes(self, obj):
        return [size.name for size in obj.sizes.all()]


    def get_category(self, obj):
        return obj.category.name if obj.category else None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["price"] = instance.price_with_markup
        return representation


class StoreCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreCategory
        fields = ["id", "name", "image", "slug"]


class ProductCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductCategory
        fields = ["id", "name", "image", "slug"]


from rest_framework import serializers
from datetime import datetime, time
from .models import OpeningHour





from .models import Product, Image, ProductCategory
from .models import Review, Wishlist
from .models import StoreType, Store

class StoreTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreType
        fields = ['id', 'name', 'description', 'icon']


class ReviewSerializer(serializers.ModelSerializer):
    user = (
        serializers.StringRelatedField()
    )  # or serializers.SerializerMethodField() for custom username

    class Meta:
        model = Review
        fields = ["id", "user", "comment", "rating", "created_at"]

class ImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'image', 'created_at']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['name']



class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # Include full product details
    product_price = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = ["id", "user", "product", "product_price", "added_at"]

    def get_product_price(self, obj):
        return obj.product.price if obj.product and obj.product.price else 0.00
    
class StoreSerializer(serializers.ModelSerializer):
    store_type = serializers.SerializerMethodField()
    logo = serializers.ImageField(required=False, allow_empty_file=True)
    license = serializers.FileField(required=False, allow_empty_file=True)
    opening_hours = OpeningHourSerializer(
        many=True, source="openinghour_set", required=False
    )
    
    class Meta:
        model = Store
        fields = "__all__"

    def get_store_type(self, store):
        store_type = store.store_type
        if store_type:
            return {
                "id": store_type.id,
                "name": store_type.name,
                "icon": self.get_store_type_icon_url(store_type),
            }
        return None

    def get_store_type_icon_url(self, store_type):
        request = self.context.get("request")
        if store_type.icon:
            icon_url = store_type.icon.url
            return request.build_absolute_uri(icon_url)
        return None

    def get_logo(self, store):  
        request = self.context.get("request")
        logo_url = store.logo.url
        return request.build_absolute_uri(logo_url)

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = "__all__"
        depth = 2  # Includes product fields

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Review
        fields = "__all__"

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'icon']