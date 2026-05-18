import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Ride(models.Model):
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
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('searching', 'Searching for Driver'),
        ('accepted', 'Accepted'),
        ('arrived', 'Driver Arrived'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    ride_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides')
    driver = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rides',
    )
    country = models.ForeignKey(
        'services.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    city = models.ForeignKey(
        'kudya_platform.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ride_type = models.CharField(max_length=20, choices=RIDE_TYPES, default='economy')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested', db_index=True)
    pickup_address = models.CharField(max_length=500)
    pickup_lat = models.DecimalField(max_digits=10, decimal_places=7)
    pickup_lng = models.DecimalField(max_digits=10, decimal_places=7)
    destination_address = models.CharField(max_length=500)
    destination_lat = models.DecimalField(max_digits=10, decimal_places=7)
    destination_lng = models.DecimalField(max_digits=10, decimal_places=7)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='ZAR')
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    duration_minutes = models.PositiveIntegerField(default=0)
    surge_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=30, default='cash')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    share_trip_token = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ride_number:
            self.ride_number = f'R{uuid.uuid4().hex[:8].upper()}'
        if not self.share_trip_token:
            self.share_trip_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.ride_number} ({self.status})'
