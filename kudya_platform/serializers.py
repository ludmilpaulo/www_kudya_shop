from rest_framework import serializers
from .models import City, Translation, PlatformModule, CountryComplianceSetting, AuditEvent


class CitySerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_code = serializers.CharField(source='country.code', read_only=True)

    class Meta:
        model = City
        fields = ['id', 'name', 'country', 'country_name', 'country_code', 'is_active']


class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
        fields = ['key', 'language', 'value', 'module']


class PlatformModuleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()

    class Meta:
        model = PlatformModule
        fields = [
            'id', 'key', 'title', 'subtitle', 'icon', 'route',
            'gradient_start', 'gradient_end', 'order', 'requires_auth',
        ]

    def get_title(self, obj):
        lang = self.context.get('language', 'en')
        t = Translation.objects.filter(
            key=f'module.{obj.key}.title',
            language=lang,
            is_active=True,
        ).first()
        if t:
            return t.value
        t_en = Translation.objects.filter(
            key=f'module.{obj.key}.title',
            language='en',
            is_active=True,
        ).first()
        return t_en.value if t_en else obj.get_key_display()

    def get_subtitle(self, obj):
        lang = self.context.get('language', 'en')
        t = Translation.objects.filter(
            key=f'module.{obj.key}.subtitle',
            language=lang,
            is_active=True,
        ).first()
        if t:
            return t.value
        t_en = Translation.objects.filter(
            key=f'module.{obj.key}.subtitle',
            language='en',
            is_active=True,
        ).first()
        return t_en.value if t_en else ''


class CountryComplianceSettingSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_code = serializers.CharField(source='country.code', read_only=True)

    class Meta:
        model = CountryComplianceSetting
        fields = [
            'id',
            'country',
            'country_name',
            'country_code',
            'online_consultations_allowed',
            'prescriptions_allowed',
            'required_doctor_documents',
            'medical_license_verification_required',
            'data_privacy_policy',
            'cancellation_policy',
            'refund_policy',
            'tax_vat_rate',
            'payment_rules',
            'patient_data_retention_days',
            'is_active',
            'updated_at',
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source='actor.email', read_only=True, allow_null=True)
    country_name = serializers.CharField(source='country.name', read_only=True, allow_null=True)
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)

    class Meta:
        model = AuditEvent
        fields = [
            'id',
            'actor',
            'actor_email',
            'action',
            'target_type',
            'target_id',
            'target_repr',
            'country',
            'country_name',
            'city',
            'city_name',
            'metadata',
            'ip_address',
            'user_agent',
            'created_at',
        ]
