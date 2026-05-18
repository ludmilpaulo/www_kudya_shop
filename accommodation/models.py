from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AccommodationListing(models.Model):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('room', 'Room'),
        ('guesthouse', 'Guesthouse'),
        ('hotel', 'Hotel'),
        ('lodge', 'Lodge'),
        ('villa', 'Villa'),
        ('student', 'Student Accommodation'),
        ('backpackers', 'Backpackers'),
        ('holiday_home', 'Holiday Home'),
        ('long_stay', 'Long-Stay'),
    ]
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accommodation_listings')
    title = models.CharField(max_length=255)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    description = models.TextField()
    country = models.ForeignKey('services.Country', on_delete=models.PROTECT)
    city = models.ForeignKey('kudya_platform.City', on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=500)
    hide_address_until_booking = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    price_per_night = models.DecimalField(max_digits=12, decimal_places=2)
    weekly_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='ZAR')
    max_guests = models.PositiveIntegerField(default=2)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    beds = models.PositiveIntegerField(default=1)
    amenities = models.JSONField(default=list, blank=True)
    rules = models.TextField(blank=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    cancellation_policy = models.TextField(blank=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending', db_index=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AccommodationImage(models.Model):
    listing = models.ForeignKey(AccommodationListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='accommodation/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class AccommodationBooking(models.Model):
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accommodation_bookings')
    listing = models.ForeignKey(AccommodationListing, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending', db_index=True)
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
