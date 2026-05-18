from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class MedicalSpecialty(models.Model):
    """Medical specialties — seeded via admin, not hardcoded in clients."""
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='stethoscope')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Medical Specialties'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    professional_title = models.CharField(max_length=100, blank=True)
    specialty = models.ForeignKey(
        MedicalSpecialty,
        on_delete=models.PROTECT,
        related_name='doctors',
    )
    years_experience = models.PositiveIntegerField(default=0)
    languages = models.CharField(
        max_length=200,
        help_text='Comma-separated language codes: en,pt,fr,es',
    )
    country = models.ForeignKey('services.Country', on_delete=models.PROTECT, related_name='doctors')
    city = models.ForeignKey(
        'kudya_platform.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctors',
    )
    clinic_name = models.CharField(max_length=200, blank=True)
    biography = models.TextField(blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    online_consultation_enabled = models.BooleanField(default=False)
    physical_consultation_enabled = models.BooleanField(default=True)
    license_number = models.CharField(max_length=100)
    conditions_treated = models.TextField(blank=True)
    services_offered = models.TextField(blank=True)
    insurance_accepted = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='doctors/photos/', blank=True)
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS,
        default='pending',
        db_index=True,
    )
    rejection_reason = models.TextField(blank=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    review_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-rating', '-created_at']

    def __str__(self):
        return f'Dr. {self.user.get_full_name() or self.user.username} — {self.specialty.name}'


class DoctorDocument(models.Model):
    DOC_TYPES = [
        ('license', 'Medical License'),
        ('qualification', 'Medical Qualification'),
        ('identity', 'Identity Document'),
        ('practice_address', 'Proof of Practice Address'),
        ('other', 'Other'),
    ]
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES)
    file = models.FileField(upload_to='doctors/documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)


class DoctorAvailability(models.Model):
    DAYS = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.IntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    consultation_type = models.CharField(
        max_length=20,
        choices=[('physical', 'Physical'), ('online', 'Online'), ('both', 'Both')],
        default='both',
    )

    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time', 'consultation_type')
        ordering = ['day_of_week', 'start_time']


class Appointment(models.Model):
    APPOINTMENT_TYPES = [
        ('physical', 'Physical Consultation'),
        ('online', 'Online Consultation'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    notes = models.TextField(blank=True)
    meeting_link = models.URLField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f'{self.customer} → {self.doctor} on {self.date}'
