from django.contrib import admin
from .models import Order, OrderDetails

# Register the OrderDetails model
@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'meal', 'quantity', 'sub_total')
    search_fields = ('order__id', 'meal__name')
    list_filter = ('order__status',)

# Inline admin for OrderDetails to be included in Order admin
class OrderDetailsInline(admin.TabularInline):
    model = OrderDetails
    extra = 1

# Register the Order model
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'restaurant', 'driver', 'address', 'total', 'status', 'created_at', 'picked_at')
    search_fields = ('customer__user__username', 'restaurant__name', 'driver__user__username', 'address')
    list_filter = ('status', 'created_at', 'picked_at')
    inlines = [OrderDetailsInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'restaurant', 'driver', 'chat')

# Register any additional configurations here

