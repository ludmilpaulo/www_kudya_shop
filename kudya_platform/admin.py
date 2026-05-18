from django.contrib import admin
from .models import City, Translation, PlatformModule, CountryComplianceSetting, AuditEvent


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'is_active']
    list_filter = ['country', 'is_active']


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ['key', 'language', 'module', 'is_active']
    list_filter = ['language', 'module', 'is_active']
    search_fields = ['key', 'value']


@admin.register(PlatformModule)
class PlatformModuleAdmin(admin.ModelAdmin):
    list_display = ['key', 'order', 'is_active', 'route']
    list_filter = ['is_active']
    filter_horizontal = ['allowed_countries']


@admin.register(CountryComplianceSetting)
class CountryComplianceSettingAdmin(admin.ModelAdmin):
    list_display = [
        'country',
        'online_consultations_allowed',
        'prescriptions_allowed',
        'medical_license_verification_required',
        'tax_vat_rate',
        'is_active',
    ]
    list_filter = [
        'online_consultations_allowed',
        'prescriptions_allowed',
        'medical_license_verification_required',
        'is_active',
    ]
    search_fields = ['country__name', 'country__code']


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ['action', 'target_type', 'target_id', 'actor', 'country', 'city', 'created_at']
    list_filter = ['action', 'target_type', 'country', 'city']
    search_fields = ['target_repr', 'target_id', 'actor__email']
    readonly_fields = [
        'actor',
        'action',
        'target_type',
        'target_id',
        'target_repr',
        'country',
        'city',
        'metadata',
        'ip_address',
        'user_agent',
        'created_at',
    ]
