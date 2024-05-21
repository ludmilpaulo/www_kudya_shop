from rest_framework import serializers
from restaurants.models import Meal, MealCategory, OpeningHour, Restaurant, RestaurantCategory
from django.contrib.auth import get_user_model
User = get_user_model()






class RestaurantSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    def get_category(self, restaurant):
        category = restaurant.category
        if category:
            return {
                'id':category.id,
                'name': category.name,
                'image': self.get_category_image_url(category),
            }
        return None

    def get_category_image_url(self, category):
        request = self.context.get('request')
        image_url = category.image.url
        return request.build_absolute_uri(image_url)

    def get_logo(self, restaurant):
        request = self.context.get('request')
        logo_url = restaurant.logo.url
        return request.build_absolute_uri(logo_url)

    class Meta:
        model = Restaurant
        #fields = '__all__'
        fields = ("id", "name", "phone", "address", "logo", "category", "barnner", "is_approved")





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