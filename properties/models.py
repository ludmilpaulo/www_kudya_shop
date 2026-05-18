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

    amenities = models.JSONField(default=list, blank=True)
    suburb = models.CharField(max_length=100, blank=True, db_index=True)
    country = models.ForeignKey(
        'services.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='properties',
    )
    deposit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    furnished = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    pet_policy = models.CharField(max_length=200, blank=True)
    available_date = models.DateField(null=True, blank=True)
    lease_term = models.CharField(max_length=100, blank=True)
    land_size_sqm = models.PositiveIntegerField(null=True, blank=True)
    building_size_sqm = models.PositiveIntegerField(null=True, blank=True)
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('suspended', 'Suspended'),
        ],
        default='pending',
        db_index=True,
    )
    is_available = models.BooleanField(default=True, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f"{self.title} ({self.get_listing_type_display()})"


class PropertyEnquiry(models.Model):
    ENQUIRY_TYPES = [
        ('general', 'General Enquiry'),
        ('viewing', 'Viewing Request'),
        ('offer', 'Offer Interest'),
        ('rental_application', 'Rental Application'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('responded', 'Responded'),
        ('scheduled', 'Viewing Scheduled'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_enquiries')
    property_listing = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='enquiries')
    enquiry_type = models.CharField(max_length=30, choices=ENQUIRY_TYPES, default='general')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Property Enquiries'
