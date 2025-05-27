# payments/models.py

from django.db import models

class PaymentProvider(models.Model):
    PROVIDER_CHOICES = [
        ('paystack', 'Paystack'),
        ('multicaixa', 'Multicaixa'),
        ('mpesa', 'Mpesa'),
        ('sibs', 'SIBS'),
    ]

    COUNTRY_CHOICES = [
        ('ZA', 'South Africa'),
        ('AO', 'Angola'),
        ('MZ', 'Mozambique'),
        ('CV', 'Cape Verde'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    public_key = models.CharField(max_length=255, blank=True, null=True)
    secret_key = models.CharField(max_length=255, blank=True, null=True)
    extra_data = models.JSONField(blank=True, null=True)  # for any additional configs

    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('provider', 'country')

    def __str__(self):
        return f"{self.get_provider_display()} ({self.get_country_display()})"
