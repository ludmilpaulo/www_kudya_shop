from rest_framework import serializers
from restaurants.models import Meal, MealCategory, OpeningHour, Restaurant, RestaurantCategory
from django.contrib.auth import get_user_model
User = get_user_model()





class OpeningHourSerializer(serializers.ModelSerializer):
    day = serializers.SerializerMethodField()

    def get_day(self, obj):
        return obj.get_day_display()

    class Meta:
        model = OpeningHour
        fields = ('day', 'from_hour', 'to_hour', 'is_closed')

class RestaurantSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    opening_hours = OpeningHourSerializer(many=True, source='openinghour_set')

    def get_category(self, restaurant):
        category = restaurant.category
        if category:
            return {
                'id': category.id,
                'name': category.name,
                'image': self.get_category_image_url(category),
            }
        return None

    def get_category_image_url(self, category):
        request = self.context.get('request')
        if category.image:
            image_url = category.image.url
            return request.build_absolute_uri(image_url)
        return None

    def get_logo(self, restaurant):
        request = self.context.get('request')
        logo_url = restaurant.logo.url
        return request.build_absolute_uri(logo_url)

    class Meta:
        model = Restaurant
        fields = ("id", "name", "phone", "address", "logo", "category", "barnner", "is_approved", "opening_hours")



class MealSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Meal
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None



class RestaurantCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantCategory
        fields = ['id', 'name', 'image', 'slug']

class MealCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MealCategory
        fields = ['id', 'name', 'image', 'slug']
        
        
class OpeningHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpeningHour
        fields = '__all__'