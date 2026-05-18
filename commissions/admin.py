from django.contrib import admin
from .models import CommissionRule


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = ['service_type', 'country', 'city', 'fee_type', 'value', 'is_active']
    list_filter = ['service_type', 'fee_type', 'is_active']
