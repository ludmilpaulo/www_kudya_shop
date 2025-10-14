# currency/admin.py
from django.contrib import admin
from .models import ExchangeRate

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'target_currency', 'rate', 'date', 'last_updated')
    list_filter = ('base_currency', 'target_currency', 'date')
    search_fields = ('target_currency',)
    readonly_fields = ('last_updated',)
    ordering = ('-date', 'target_currency')

