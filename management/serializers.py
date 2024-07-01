from rest_framework import serializers
from .models import  RestaurantUser

c

class RestaurantUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantUser
        fields = '__all__'
