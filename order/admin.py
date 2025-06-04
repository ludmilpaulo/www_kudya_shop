from django.contrib import admin
from .models import Coupon, Order, OrderDetails

class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "discount_percentage", "order_count")
    search_fields = ("code", "user__username", "user__email")
    list_filter = ("discount_percentage",)
    readonly_fields = ("order_count",)

class OrderDetailsInline(admin.TabularInline):
    model = OrderDetails
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "store",
        "driver",
        "total",
        "discount_amount",
        "delivery_fee",
        "status",
        "payment_method",
        "created_at",
        "payment_status_store",
        "payment_status_driver",
        "secret_pin",
    )
    list_filter = (
        "status",
        "payment_method",
        "created_at",
        "payment_status_store",
        "payment_status_driver",
        "store",
        "driver",
    )
    search_fields = (
        "id",
        "customer__user__username",
        "customer__user__email",
        "driver__user__username",
        "store__name",
        "address",
        "secret_pin",
    )
    inlines = [OrderDetailsInline]
    readonly_fields = (
        "created_at",
        "picked_at",
        "invoice_pdf",
        "secret_pin",
        "driver_commission",
        "original_price",
        "discount_amount",
        "delivery_fee",
        "loyalty_discount",
    )
    fieldsets = (
        ("Order Info", {
            "fields": (
                "customer",
                "store",
                "driver",
                "address",
                "location",
                "delivery_notes",
                "order_details",
            )
        }),
        ("Payment & Status", {
            "fields": (
                "total",
                "original_price",
                "discount_amount",
                "coupon",
                "delivery_fee",
                "status",
                "payment_method",
                "payment_status_store",
                "payment_status_driver",
                "proof_of_payment_store",
                "proof_of_payment_driver",
            )
        }),
        ("Meta", {
            "fields": (
                "created_at",
                "picked_at",
                "secret_pin",
                "driver_commission_percentage",
                "driver_commission",
                "invoice_pdf",
            )
        }),
    )

    def get_queryset(self, request):
        # Optimize queries
        qs = super().get_queryset(request)
        return qs.select_related("customer__user", "store", "driver__user", "coupon")

class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "sub_total")
    search_fields = ("order__id", "product__name")
    list_filter = ("product",)

admin.site.register(Coupon, CouponAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderDetails, OrderDetailsAdmin)

