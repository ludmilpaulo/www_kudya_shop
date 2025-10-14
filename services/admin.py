from django.contrib import admin
from .models import (
    Country, Province, ServiceCategory, Service, ServiceAvailability,
    BlackoutDate, Booking, ServiceReview, ParceirKYC, PayoutRequest,
    ParceiroEarnings
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'code', 'is_active']
    list_filter = ['country', 'is_active']
    search_fields = ['name', 'code']


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'requires_license', 'requires_region_verification', 'is_active', 'order']
    list_filter = ['category_type', 'requires_license', 'requires_region_verification', 'is_active']
    search_fields = ['name', 'name_pt']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'parceiro', 'category', 'price', 'duration_minutes', 'delivery_type', 'is_active', 'is_featured']
    list_filter = ['category', 'delivery_type', 'is_active', 'is_featured', 'instant_booking']
    search_fields = ['title', 'title_pt', 'description', 'parceiro__name']
    filter_horizontal = ['allowed_countries', 'allowed_provinces']
    date_hierarchy = 'created_at'


@admin.register(ServiceAvailability)
class ServiceAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['service', 'day_of_week', 'specific_date', 'start_time', 'end_time', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'is_recurring']
    search_fields = ['service__title']


@admin.register(BlackoutDate)
class BlackoutDateAdmin(admin.ModelAdmin):
    list_display = ['service', 'start_date', 'end_date', 'reason']
    list_filter = ['start_date', 'end_date']
    search_fields = ['service__title', 'reason']
    date_hierarchy = 'start_date'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_number', 'service', 'customer', 'booking_date', 'booking_time', 'status', 'payment_status', 'price']
    list_filter = ['status', 'payment_status', 'booking_date']
    search_fields = ['booking_number', 'service__title', 'customer__user__username']
    date_hierarchy = 'booking_date'
    readonly_fields = ['booking_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_number', 'service', 'customer', 'booking_date', 'booking_time', 'duration_minutes')
        }),
        ('Location', {
            'fields': ('customer_location', 'customer_latitude', 'customer_longitude')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'payment_method')
        }),
        ('Pricing', {
            'fields': ('price', 'platform_fee', 'provider_earnings')
        }),
        ('Notes & Communication', {
            'fields': ('customer_notes', 'provider_notes', 'cancellation_reason')
        }),
        ('Proof & Verification', {
            'fields': ('completion_photo', 'customer_signature')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'completed_at')
        }),
    )


@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ['service', 'customer', 'rating', 'created_at', 'helpful_count']
    list_filter = ['rating', 'created_at']
    search_fields = ['service__title', 'customer__user__username', 'comment']
    date_hierarchy = 'created_at'


@admin.register(ParceirKYC)
class ParceirKYCAdmin(admin.ModelAdmin):
    list_display = ['parceiro', 'full_legal_name', 'status', 'is_verified', 'submitted_at']
    list_filter = ['status', 'is_verified', 'id_document_type']
    search_fields = ['parceiro__name', 'full_legal_name', 'id_document_number']
    date_hierarchy = 'submitted_at'
    readonly_fields = ['submitted_at', 'updated_at', 'verified_at']
    
    fieldsets = (
        ('Parceiro Information', {
            'fields': ('parceiro', 'full_legal_name', 'date_of_birth', 'nationality')
        }),
        ('Documents', {
            'fields': ('id_document_type', 'id_document_number', 'id_document_front', 'id_document_back', 
                      'professional_license', 'business_license', 'tax_certificate', 'selfie_photo')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_holder_name', 'account_number', 'iban', 'swift_code')
        }),
        ('Verification Status', {
            'fields': ('status', 'is_verified', 'rejection_reason', 'admin_notes', 'verified_by', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at')
        }),
    )
    
    actions = ['approve_kyc', 'reject_kyc']
    
    def approve_kyc(self, request, queryset):
        for kyc in queryset:
            kyc.approve(request.user)
        self.message_user(request, f"{queryset.count()} KYC(s) approved successfully.")
    approve_kyc.short_description = "Approve selected KYC verifications"
    
    def reject_kyc(self, request, queryset):
        for kyc in queryset:
            kyc.reject("Rejected by admin")
        self.message_user(request, f"{queryset.count()} KYC(s) rejected.")
    reject_kyc.short_description = "Reject selected KYC verifications"


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ['parceiro', 'amount', 'currency', 'status', 'requested_at', 'processed_at']
    list_filter = ['status', 'currency', 'requested_at']
    search_fields = ['parceiro__name', 'transaction_reference']
    date_hierarchy = 'requested_at'
    readonly_fields = ['requested_at', 'processed_at', 'completed_at']
    
    actions = ['mark_as_completed', 'mark_as_processing']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='completed', completed_at=timezone.now(), processed_by=request.user)
        self.message_user(request, f"{queryset.count()} payout(s) marked as completed.")
    mark_as_completed.short_description = "Mark selected payouts as completed"
    
    def mark_as_processing(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='processing', processed_at=timezone.now(), processed_by=request.user)
        self.message_user(request, f"{queryset.count()} payout(s) marked as processing.")
    mark_as_processing.short_description = "Mark selected payouts as processing"


@admin.register(ParceiroEarnings)
class ParceiroEarningsAdmin(admin.ModelAdmin):
    list_display = ['parceiro', 'earning_type', 'gross_amount', 'platform_fee', 'net_amount', 'is_paid_out', 'earned_at']
    list_filter = ['earning_type', 'is_paid_out', 'earned_at']
    search_fields = ['parceiro__name']
    date_hierarchy = 'earned_at'
    readonly_fields = ['earned_at', 'paid_out_at']
