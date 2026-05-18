from django.contrib import admin
from .models import PackageDelivery


@admin.register(PackageDelivery)
class PackageDeliveryAdmin(admin.ModelAdmin):
    list_display = ['delivery_number', 'customer', 'courier', 'package_type', 'status', 'price']
