from django.contrib import admin
from .models import AccommodationListing, AccommodationImage, AccommodationBooking


class AccommodationImageInline(admin.TabularInline):
    model = AccommodationImage
    extra = 1


@admin.register(AccommodationListing)
class AccommodationListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'host', 'city', 'price_per_night', 'approval_status']
    list_filter = ['approval_status', 'property_type', 'country']
    inlines = [AccommodationImageInline]


@admin.register(AccommodationBooking)
class AccommodationBookingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'listing', 'check_in', 'check_out', 'booking_status', 'payment_status']
