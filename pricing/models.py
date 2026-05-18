from django.db import models


class PricingRule(models.Model):
    SERVICE_TYPES = [
        ('ride', 'Ride'),
        ('food_delivery', 'Food Delivery'),
        ('grocery_delivery', 'Grocery Delivery'),
        ('package', 'Package Delivery'),
        ('rental', 'Car Rental'),
    ]
    RIDE_TYPES = [
        ('economy', 'Economy'),
        ('comfort', 'Comfort'),
        ('premium', 'Premium'),
        ('xl', 'XL'),
        ('bike', 'Bike'),
        ('delivery_bike', 'Delivery Bike'),
        ('women', 'Women Preferred'),
        ('scheduled', 'Scheduled'),
    ]

    service_type = models.CharField(max_length=30, choices=SERVICE_TYPES, db_index=True)
    ride_type = models.CharField(max_length=20, choices=RIDE_TYPES, blank=True)
    country = models.ForeignKey(
        'services.Country',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    city = models.ForeignKey('kudya_platform.City', on_delete=models.CASCADE, null=True, blank=True)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=25)
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2, default=8)
    per_minute_rate = models.DecimalField(max_digits=10, decimal_places=2, default=1.5)
    minimum_fare = models.DecimalField(max_digits=10, decimal_places=2, default=35)
    delivery_base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=20)
    service_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    surge_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['service_type', 'country']
