import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PackageDelivery(models.Model):
    PACKAGE_TYPES = [
        ('envelope', 'Small Envelope'),
        ('small', 'Small Parcel'),
        ('medium', 'Medium Parcel'),
        ('large', 'Large Parcel'),
        ('fragile', 'Fragile Item'),
        ('document', 'Document Delivery'),
    ]
    URGENCY_CHOICES = [
        ('standard', 'Standard'),
        ('express', 'Express'),
        ('same_day', 'Same Day'),
    ]
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('searching', 'Searching Courier'),
        ('accepted', 'Accepted'),
        ('pickup_confirmed', 'Pickup Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    delivery_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='package_deliveries')
    courier = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='package_deliveries',
    )
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, default='small')
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='standard')
    pickup_address = models.CharField(max_length=500)
    pickup_lat = models.DecimalField(max_digits=10, decimal_places=7)
    pickup_lng = models.DecimalField(max_digits=10, decimal_places=7)
    dropoff_address = models.CharField(max_length=500)
    dropoff_lat = models.DecimalField(max_digits=10, decimal_places=7)
    dropoff_lng = models.DecimalField(max_digits=10, decimal_places=7)
    recipient_name = models.CharField(max_length=200)
    recipient_phone = models.CharField(max_length=30)
    package_notes = models.TextField(blank=True)
    package_photo = models.ImageField(upload_to='packages/', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='ZAR')
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested', db_index=True)
    payment_status = models.CharField(max_length=20, default='pending')
    proof_of_pickup = models.ImageField(upload_to='package_proofs/', blank=True)
    proof_of_delivery = models.ImageField(upload_to='package_proofs/', blank=True)
    pickup_otp = models.CharField(max_length=6, blank=True)
    delivery_otp = models.CharField(max_length=6, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = f'P{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)
