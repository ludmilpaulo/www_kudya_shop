from django.db import models


class CommissionRule(models.Model):
    SERVICE_TYPES = [
        ('food', 'Food Delivery'),
        ('grocery', 'Grocery'),
        ('ride', 'Ride Hailing'),
        ('package', 'Package Delivery'),
        ('car_rental', 'Car Rental'),
        ('doctor', 'Doctor Booking'),
        ('service', 'Professional Service'),
        ('accommodation', 'Accommodation'),
        ('rental_lead', 'Long-Term Rental Lead'),
        ('property_sale', 'Property Sale Lead'),
    ]
    FEE_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Fee'),
        ('subscription', 'Monthly Subscription'),
        ('per_lead', 'Pay Per Lead'),
        ('featured', 'Featured Listing Fee'),
    ]

    country = models.ForeignKey(
        'services.Country',
        on_delete=models.CASCADE,
        related_name='commission_rules',
        null=True,
        blank=True,
    )
    city = models.ForeignKey(
        'kudya_platform.City',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPES)
    provider_type = models.CharField(max_length=50, blank=True)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES, default='percentage')
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text='Percentage or fixed amount')
    currency = models.CharField(max_length=3, default='ZAR')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['service_type', 'country']

    def __str__(self):
        return f'{self.service_type} — {self.fee_type}: {self.value}'
