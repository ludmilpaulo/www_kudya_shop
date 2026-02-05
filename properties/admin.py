from django.contrib import admin
from .models import Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'listing_type', 'property_type', 'city', 'price', 'is_approved', 'is_available']
    list_filter = ['listing_type', 'property_type', 'is_approved', 'is_available']
    search_fields = ['title', 'address', 'city']
    inlines = [PropertyImageInline]
