from django.contrib import admin
from .models import MedicalSpecialty, DoctorProfile, DoctorDocument, DoctorAvailability, Appointment


@admin.register(MedicalSpecialty)
class MedicalSpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


class DoctorDocumentInline(admin.TabularInline):
    model = DoctorDocument
    extra = 0


class DoctorAvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    extra = 0


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'country', 'approval_status', 'rating', 'is_active']
    list_filter = ['approval_status', 'specialty', 'country']
    inlines = [DoctorDocumentInline, DoctorAvailabilityInline]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'doctor', 'date', 'start_time', 'status', 'payment_status']
    list_filter = ['status', 'payment_status', 'appointment_type']
