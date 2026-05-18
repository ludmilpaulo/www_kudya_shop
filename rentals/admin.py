from django.contrib import admin
from .models import RentalVehicle, RentalVehicleImage, RentalBooking


class RentalVehicleImageInline(admin.TabularInline):
    model = RentalVehicleImage
    extra = 1


@admin.register(RentalVehicle)
class RentalVehicleAdmin(admin.ModelAdmin):
    list_display = ['make', 'model', 'partner', 'daily_price', 'status', 'is_approved']
    inlines = [RentalVehicleImageInline]


@admin.register(RentalBooking)
class RentalBookingAdmin(admin.ModelAdmin):
    list_display = ['booking_number', 'customer', 'vehicle', 'status', 'total_amount']
