import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class RentalVehicle(models.Model):
    TRANSMISSION = [('manual', 'Manual'), ('automatic', 'Automatic')]
    FUEL_TYPES = [('petrol', 'Petrol'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')]
    STATUS = [('available', 'Available'), ('rented', 'Rented'), ('maintenance', 'Maintenance')]

    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_vehicles')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    plate_number = models.CharField(max_length=20)
    color = models.CharField(max_length=50, blank=True)
    seats = models.PositiveIntegerField(default=4)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION, default='automatic')
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES, default='petrol')
    city = models.ForeignKey('kudya_platform.City', on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey('services.Country', on_delete=models.PROTECT)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2)
    weekly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='ZAR')
    status = models.CharField(max_length=20, choices=STATUS, default='available')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.make} {self.model} ({self.plate_number})'


class RentalVehicleImage(models.Model):
    vehicle = models.ForeignKey(RentalVehicle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='rental_vehicles/')
    order = models.PositiveIntegerField(default=0)


class RentalBooking(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]

    booking_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_bookings')
    vehicle = models.ForeignKey(RentalVehicle, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    pickup_location = models.CharField(max_length=500)
    return_location = models.CharField(max_length=500)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    status = models.CharField(max_length=20, choices=STATUS, default='pending', db_index=True)
    payment_status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_number:
            self.booking_number = f'CR{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)
