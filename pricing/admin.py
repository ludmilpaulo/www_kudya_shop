from django.contrib import admin
from .models import PricingRule


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ['service_type', 'ride_type', 'country', 'city', 'base_fare', 'is_active']
