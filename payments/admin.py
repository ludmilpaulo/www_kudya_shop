from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['email', 'country', 'amount', 'currency', 'created_at', 'status']
    search_fields = ['email', 'provider_reference']
