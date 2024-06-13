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
        fields = ("id", "name", "phone", "address", "logo", "category", "barnner", "is_approved", "opening_hours","location")




class MealSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Meal
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_category(self, obj):
        return obj.category.name if obj.category else None


class RestaurantCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantCategory
        fields = ['id', 'name', 'image', 'slug']

class MealCategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = MealCategory
        fields = ['id', 'name', 'image', 'slug']



from rest_framework import serializers
from datetime import datetime, time
from .models import OpeningHour

class OpeningHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpeningHour
        fields = '__all__'

    HOUR_OF_DAY_24 = [(time(h, m).strftime('%I:%M %p'), time(h, m).strftime('%I:%M %p')) for h in range(24) for m in (0, 30)]
    
    def validate_from_hour(self, value):
        return self.convert_and_validate_time(value, 'from_hour')

    def validate_to_hour(self, value):
        return self.convert_and_validate_time(value, 'to_hour')

    def convert_and_validate_time(self, time_str, field_name):
        # Define the expected time format
        time_format = '%I:%M %p'
        try:
            # Convert the time string to the correct format with leading zeros
            valid_time = datetime.strptime(time_str, time_format).strftime(time_format)
            # Log the conversion for debugging
            print(f"Converting {field_name}: {time_str} -> {valid_time}")
            # Check if the time is in HOUR_OF_DAY_24 choices
            if valid_time not in dict(self.HOUR_OF_DAY_24):
                print(f"{valid_time} is not a valid choice in HOUR_OF_DAY_24")
                raise serializers.ValidationError(f'"{valid_time}" não é um escolha válido.')
            return valid_time
        except ValueError:
            raise serializers.ValidationError(f'"{time_str}" não é um escolha válido.')

    def validate(self, data):
        print(f"Validating data: {data}")
        data['from_hour'] = self.convert_and_validate_time(data.get('from_hour', ''), 'from_hour')
        data['to_hour'] = self.convert_and_validate_time(data.get('to_hour', ''), 'to_hour')
        print(f"Post-validation data: {data}")
        return data

