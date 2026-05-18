from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from .models import MedicalSpecialty, DoctorProfile, DoctorAvailability, DoctorDocument, Appointment
from kudya_platform.models import CountryComplianceSetting

User = get_user_model()


class MedicalSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalSpecialty
        fields = ['id', 'slug', 'name', 'icon', 'order']


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DoctorAvailability
        fields = [
            'id', 'day_of_week', 'day_name', 'start_time', 'end_time',
            'is_available', 'consultation_type',
        ]


class DoctorListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    specialty_name = serializers.CharField(source='specialty.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)
    country_name = serializers.CharField(source='country.name', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'name', 'professional_title', 'specialty', 'specialty_name',
            'years_experience', 'languages', 'country', 'country_name',
            'city', 'city_name', 'clinic_name', 'consultation_fee', 'currency',
            'online_consultation_enabled', 'physical_consultation_enabled',
            'rating', 'review_count', 'profile_photo',
        ]

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class DoctorDetailSerializer(DoctorListSerializer):
    availability = DoctorAvailabilitySerializer(many=True, read_only=True)
    biography = serializers.CharField()
    conditions_treated = serializers.CharField()
    services_offered = serializers.CharField()
    insurance_accepted = serializers.CharField()

    class Meta(DoctorListSerializer.Meta):
        fields = DoctorListSerializer.Meta.fields + [
            'biography', 'conditions_treated', 'services_offered',
            'insurance_accepted', 'availability',
        ]


class DoctorRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            'email', 'password', 'first_name', 'last_name',
            'professional_title', 'specialty', 'years_experience', 'languages',
            'country', 'city', 'clinic_name', 'biography', 'consultation_fee',
            'currency', 'online_consultation_enabled', 'physical_consultation_enabled',
            'license_number', 'conditions_treated', 'services_offered',
            'insurance_accepted',
        ]

    def validate(self, attrs):
        country = attrs.get('country')
        if attrs.get('online_consultation_enabled') and country:
            settings = CountryComplianceSetting.objects.filter(
                country=country,
                is_active=True,
            ).first()
            if not settings or not settings.online_consultations_allowed:
                raise serializers.ValidationError({
                    'online_consultation_enabled': 'Online consultations are not enabled in this country.'
                })
        return attrs

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        user, _ = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'first_name': first_name, 'last_name': last_name},
        )
        if not user.check_password(password):
            user.set_password(password)
            user.save()
        user.role = 'doctor'
        user.country = validated_data.get('country')
        user.city = validated_data.get('city')
        user.save(update_fields=['role', 'country', 'city'])
        return DoctorProfile.objects.create(user=user, **validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    specialty_name = serializers.CharField(source='doctor.specialty.name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_name', 'specialty_name', 'appointment_type',
            'date', 'start_time', 'end_time', 'status', 'consultation_fee',
            'currency', 'payment_status', 'notes', 'meeting_link', 'created_at',
        ]
        read_only_fields = ['status', 'payment_status', 'meeting_link', 'created_at']

    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username


class AppointmentBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'doctor', 'appointment_type', 'date', 'start_time', 'end_time', 'notes',
        ]

    def validate(self, attrs):
        doctor = attrs['doctor']
        appointment_type = attrs['appointment_type']
        appointment_date = attrs['date']
        start_time = attrs['start_time']
        end_time = attrs['end_time']

        if doctor.approval_status != 'approved' or not doctor.is_active:
            raise serializers.ValidationError({'doctor': 'Doctor is not available for booking.'})

        if appointment_type == 'online' and not doctor.online_consultation_enabled:
            raise serializers.ValidationError({'appointment_type': 'Doctor does not offer online consultations.'})
        if appointment_type == 'physical' and not doctor.physical_consultation_enabled:
            raise serializers.ValidationError({'appointment_type': 'Doctor does not offer physical consultations.'})

        if appointment_date < timezone.localdate():
            raise serializers.ValidationError({'date': 'Appointment date cannot be in the past.'})

        if start_time >= end_time:
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})

        if appointment_type == 'online':
            settings = CountryComplianceSetting.objects.filter(
                country=doctor.country,
                is_active=True,
            ).first()
            if not settings or not settings.online_consultations_allowed:
                raise serializers.ValidationError({
                    'appointment_type': 'Online consultations are not enabled in this country.'
                })

        has_matching_availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=appointment_date.weekday(),
            is_available=True,
            start_time__lte=start_time,
            end_time__gte=end_time,
        ).filter(
            Q(consultation_type='both') | Q(consultation_type=appointment_type)
        ).exists()
        if not has_matching_availability:
            raise serializers.ValidationError({'start_time': 'Selected slot is outside doctor availability.'})

        has_conflict = Appointment.objects.filter(
            doctor=doctor,
            date=appointment_date,
            status__in=['pending', 'confirmed', 'in_progress'],
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()
        if has_conflict:
            raise serializers.ValidationError({'start_time': 'Selected slot is already booked.'})

        return attrs

    def create(self, validated_data):
        doctor = validated_data['doctor']
        validated_data['customer'] = self.context['request'].user
        validated_data['consultation_fee'] = doctor.consultation_fee
        validated_data['currency'] = doctor.currency
        return super().create(validated_data)
