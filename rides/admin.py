from django.contrib import admin
from .models import Ride


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ['ride_number', 'customer', 'driver', 'ride_type', 'status', 'estimated_price', 'created_at']
    list_filter = ['status', 'ride_type', 'payment_status']
