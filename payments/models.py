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


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('wallet', 'Wallet'),
        ('apple_pay', 'Apple Pay'),
        ('google_pay', 'Google Pay'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    user = models.ForeignKey('contas.User', on_delete=models.CASCADE, related_name='payments')
    service_type = models.CharField(max_length=50, db_index=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='card')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    provider_reference = models.CharField(max_length=255, blank=True)
    provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.service_type} — {self.amount} {self.currency} ({self.status})'
