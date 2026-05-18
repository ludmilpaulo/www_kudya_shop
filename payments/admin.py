from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'service_type', 'amount', 'currency', 'method', 'status', 'created_at']
    search_fields = ['user__email', 'provider_reference', 'service_type']
