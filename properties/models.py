from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PropertyImage(models.Model):
    """Images for property listings"""
    image = models.ImageField(upload_to='property_images/', blank=True)
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='images')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class Property(models.Model):
    """Airbnb-style property for rent (daily/monthly) or sale"""
    LISTING_TYPE_CHOICES = [
        ('rent_daily', 'Rent per Day'),
        ('rent_monthly', 'Rent per Month'),
        ('buy', 'For Sale'),
    ]
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('studio', 'Studio'),
        ('villa', 'Villa'),
        ('room', 'Room'),
        ('other', 'Other'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES, db_index=True)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='apartment')

    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='AOA')

    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    area_sqm = models.PositiveIntegerField(null=True, blank=True, help_text='Area in square meters')

    amenities = models.JSONField(default=list, blank=True)  # e.g. ["wifi", "parking", "pool"]

    is_available = models.BooleanField(default=True, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f"{self.title} ({self.get_listing_type_display()})"
