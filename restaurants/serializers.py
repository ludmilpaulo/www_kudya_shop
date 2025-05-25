from rest_framework import serializers
from restaurants.models import (
    Meal,
    MealCategory,
    OpeningHour,
    Restaurant,
    RestaurantCategory,
)
from django.contrib.auth import get_user_model

from restaurants.models.product import Size, ProductCategory

User = get_user_model()


class OpeningHourSerializer(serializers.ModelSerializer):
    day = serializers.SerializerMethodField()

    def get_day(self, obj):
        return obj.get_day_display()

    class Meta:
        model = OpeningHour
        fields = ("day", "from_hour", "to_hour", "is_closed")


class RestaurantSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    logo = serializers.ImageField(required=False, allow_empty_file=True)
    restaurant_license = serializers.FileField(required=False, allow_empty_file=True)
    opening_hours = OpeningHourSerializer(
        many=True, source="openinghour_set", required=False
    )

    def get_category(self, restaurant):
        category = restaurant.category
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

    def get_logo(self, restaurant):
        request = self.context.get("request")
        logo_url = restaurant.logo.url
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
        if "restaurant_license" in validated_data:
            instance.restaurant_license = validated_data["restaurant_license"]

        instance.save()
        return instance

    class Meta:
        model = Restaurant
        fields = (
            "id",
            "name",
            "phone",
            "address",
            "logo",
            "restaurant_license",
            "category",
            "barnner",
            "is_approved",
            "opening_hours",
            "location",
        )


class MealSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Meal
        fields = "__all__"

    def get_image_url(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_category(self, obj):
        return obj.category.name if obj.category else None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["price"] = instance.price_with_markup
        return representation


class RestaurantCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantCategory
        fields = ["id", "name", "image", "slug"]


class MealCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = MealCategory
        fields = ["id", "name", "image", "slug"]


from rest_framework import serializers
from datetime import datetime, time
from .models import OpeningHour


class OpeningHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpeningHour
        fields = "__all__"

    HOUR_OF_DAY_24 = [
        (time(h, m).strftime("%I:%M %p"), time(h, m).strftime("%I:%M %p"))
        for h in range(24)
        for m in (0, 30)
    ]

    def validate_from_hour(self, value):
        return self.convert_and_validate_time(value, "from_hour")

    def validate_to_hour(self, value):
        return self.convert_and_validate_time(value, "to_hour")

    def convert_and_validate_time(self, time_str, field_name):
        # Define the expected time format
        time_format = "%I:%M %p"
        try:
            # Convert the time string to the correct format with leading zeros
            valid_time = datetime.strptime(time_str, time_format).strftime(time_format)
            # Log the conversion for debugging
            print(f"Converting {field_name}: {time_str} -> {valid_time}")
            # Check if the time is in HOUR_OF_DAY_24 choices
            if valid_time not in dict(self.HOUR_OF_DAY_24):
                print(f"{valid_time} is not a valid choice in HOUR_OF_DAY_24")
                raise serializers.ValidationError(
                    f'"{valid_time}" não é um escolha válido.'
                )
            return valid_time
        except ValueError:
            raise serializers.ValidationError(f'"{time_str}" não é um escolha válido.')

    def validate(self, data):
        print(f"Validating data: {data}")
        data["from_hour"] = self.convert_and_validate_time(
            data.get("from_hour", ""), "from_hour"
        )
        data["to_hour"] = self.convert_and_validate_time(
            data.get("to_hour", ""), "to_hour"
        )
        print(f"Post-validation data: {data}")
        return data




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

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    sizes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",      # Will output price_with_markup via to_representation
            "category",
            "stock",
            "on_sale",
            "bulk_sale",
            "discount_percentage",
            "season",
            "images",     # Already returns full URLs if your ImageSerializer does so
            "gender",
            "sizes",
        ]

    def get_sizes(self, obj):
        return [size.name for size in obj.sizes.all()]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Return price_with_markup as price
        rep["price"] = str(instance.price_with_markup)
        return rep


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