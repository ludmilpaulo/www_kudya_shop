from django.db import models
from django.conf import settings


class City(models.Model):
    """City within a country (links to services.Country)."""
    country = models.ForeignKey(
        'services.Country',
        on_delete=models.CASCADE,
        related_name='cities',
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Cities'
        unique_together = ('country', 'name')
        ordering = ['country', 'name']

    def __str__(self):
        return f'{self.name}, {self.country.name}'


class Translation(models.Model):
    """API-driven translations for all Kudya clients."""
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('pt', 'Portuguese'),
        ('fr', 'French'),
        ('es', 'Spanish'),
    ]

    key = models.CharField(max_length=200, db_index=True)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, db_index=True)
    value = models.TextField()
    module = models.CharField(max_length=50, default='common', db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('key', 'language', 'module')
        ordering = ['module', 'key']

    def __str__(self):
        return f'{self.key} ({self.language})'


class PlatformModule(models.Model):
    """Home screen service cards — all business data from API."""
    MODULE_KEYS = [
        ('food', 'Food'),
        ('groceries', 'Groceries'),
        ('rides', 'Rides'),
        ('package', 'Send Package'),
        ('car_rental', 'Car Rental'),
        ('doctors', 'Doctors'),
        ('services', 'Services'),
        ('accommodation', 'Accommodation'),
        ('property', 'Property'),
        ('wallet', 'Wallet'),
        ('business', 'Business'),
    ]

    key = models.CharField(max_length=30, choices=MODULE_KEYS, unique=True)
    icon = models.CharField(max_length=50, default='grid')
    route = models.CharField(max_length=100, help_text='Client navigation route')
    gradient_start = models.CharField(max_length=7, default='#3B82F6')
    gradient_end = models.CharField(max_length=7, default='#1D4ED8')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    requires_auth = models.BooleanField(default=False)
    allowed_countries = models.ManyToManyField(
        'services.Country',
        blank=True,
        related_name='platform_modules',
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.get_key_display()


class CountryComplianceSetting(models.Model):
    """Country-specific operational and healthcare rules."""

    country = models.OneToOneField(
        'services.Country',
        on_delete=models.CASCADE,
        related_name='compliance_settings',
    )
    online_consultations_allowed = models.BooleanField(default=False)
    prescriptions_allowed = models.BooleanField(default=False)
    required_doctor_documents = models.JSONField(default=list, blank=True)
    medical_license_verification_required = models.BooleanField(default=True)
    data_privacy_policy = models.TextField(blank=True)
    cancellation_policy = models.TextField(blank=True)
    refund_policy = models.TextField(blank=True)
    tax_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    payment_rules = models.JSONField(default=dict, blank=True)
    patient_data_retention_days = models.PositiveIntegerField(default=3650)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['country__name']

    def __str__(self):
        return f'{self.country.name} compliance'


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
    )
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=100, db_index=True)
    target_id = models.CharField(max_length=100, blank=True, db_index=True)
    target_repr = models.CharField(max_length=255, blank=True)
    country = models.ForeignKey(
        'services.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
    )
    city = models.ForeignKey(
        'kudya_platform.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
    )
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} {self.target_type}:{self.target_id}'
