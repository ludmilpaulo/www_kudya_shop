from email.message import EmailMessage
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Driver(models.Model):
    """Driver/Delivery Partner model"""
    VEHICLE_TYPES = [
        ('motorcycle', 'Motorcycle'),
        ('car', 'Car'),
        ('van', 'Van'),
        ('truck', 'Truck'),
        ('bicycle', 'Bicycle'),
        ('on_foot', 'On Foot'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="driver", verbose_name="Utilizador"
    )
    avatar = models.ImageField(upload_to="driver/", blank=True)
    phone = models.CharField(max_length=500, blank=True, verbose_name="telefone")
    address = models.CharField(max_length=500, blank=True, verbose_name="Endereço")
    
    # Bank Details
    bank = models.CharField(max_length=500, blank=True, verbose_name="bank")
    account_number = models.CharField(max_length=500, blank=True, verbose_name="account")
    iban = models.CharField(max_length=500, blank=True, verbose_name="iban")
    
    # Vehicle Information
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='motorcycle')
    plate = models.CharField(max_length=500, blank=True, verbose_name="Matricula")
    make = models.CharField(max_length=500, blank=True, verbose_name="Model")
    vehicle_color = models.CharField(max_length=50, blank=True)
    vehicle_photo = models.ImageField(upload_to="driver/vehicles/", blank=True)
    
    # Service Area
    service_city = models.CharField(max_length=200, blank=True)
    service_radius_km = models.IntegerField(default=10, help_text="Service radius in kilometers")
    
    # Location (current)
    location = models.CharField(max_length=500, blank=True, verbose_name="localização")
    current_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Online Status
    is_online = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True, help_text="Available to accept new deliveries")
    is_verified = models.BooleanField(default=False)
    
    # Performance Metrics
    total_deliveries = models.IntegerField(default=0)
    completed_deliveries = models.IntegerField(default=0)
    rejected_orders = models.IntegerField(default=0, verbose_name="Pedidos Rejeitados")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Motorista"
        verbose_name_plural = "Motoristas"

    def __str__(self):
        return self.user.get_username()

    def increment_rejected_orders(self):
        self.rejected_orders += 1
        self.save()
        if self.rejected_orders >= 10:
            self.send_rejection_warning_email()

    def send_rejection_warning_email(self):
        logger.info(f"Sending rejection warning email for driver {self.id}")
        context = {
            "driver_name": self.user.get_full_name(),
            "rejected_count": self.rejected_orders,
        }
        subject = "Aviso: Você atingiu o limite de rejeições de pedidos"
        message = render_to_string("email_templates/rejection_warning.html", context)
        email = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
        )
        email.content_subtype = "html"
        email.send()
        logger.info(f"Rejection warning email sent for driver {self.id}")

    def update_location(self, latitude, longitude):
        """Update driver's current location"""
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])

    def calculate_earnings(self, period='all'):
        """Calculate driver earnings for a period"""
        from order.models import Order
        
        orders = Order.objects.filter(driver=self, status=Order.DELIVERED)
        
        if period == 'today':
            orders = orders.filter(created_at__date=timezone.now().date())
        elif period == 'week':
            orders = orders.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
        elif period == 'month':
            orders = orders.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
        
        total_earnings = sum(order.driver_commission for order in orders)
        return total_earnings


class DriverLocation(models.Model):
    """Track driver location history for delivery tracking"""
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='location_history')
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    speed = models.FloatField(null=True, blank=True, help_text="Speed in km/h")
    heading = models.FloatField(null=True, blank=True, help_text="Direction in degrees")
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    # Associated delivery
    delivery_request = models.ForeignKey('DeliveryRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='location_updates')

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['driver', '-recorded_at']),
            models.Index(fields=['delivery_request', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.driver.user.username} - {self.recorded_at}"


class DeliveryRequest(models.Model):
    """Delivery request/assignment for drivers"""
    REQUEST_TYPES = [
        ('order', 'Product Order'),
        ('service', 'Service-related Delivery'),
        ('ride', 'Ride Service'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Assignment'),
        ('assigned', 'Assigned to Driver'),
        ('accepted', 'Accepted by Driver'),
        ('rejected', 'Rejected by Driver'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('arrived', 'Arrived at Destination'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # Core Information
    request_number = models.CharField(max_length=20, unique=True, editable=False)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, default='order')
    
    # References
    order = models.OneToOneField('order.Order', on_delete=models.CASCADE, null=True, blank=True, related_name='delivery_request')
    service_booking = models.ForeignKey('services.Booking', on_delete=models.CASCADE, null=True, blank=True, related_name='delivery_requests')
    
    # Driver Assignment
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True, related_name='delivery_requests')
    
    # Locations
    pickup_address = models.CharField(max_length=500)
    pickup_latitude = models.DecimalField(max_digits=10, decimal_places=7)
    pickup_longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    delivery_address = models.CharField(max_length=500)
    delivery_latitude = models.DecimalField(max_digits=10, decimal_places=7)
    delivery_longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Distance & Pricing
    estimated_distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    driver_commission = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Notes & Instructions
    pickup_instructions = models.TextField(blank=True)
    delivery_instructions = models.TextField(blank=True)
    special_requirements = models.CharField(max_length=200, blank=True)
    
    # Proof of Delivery
    proof_photo = models.ImageField(upload_to='delivery_proofs/', blank=True)
    customer_signature = models.ImageField(upload_to='delivery_signatures/', blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Ratings
    customer_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, 
        blank=True
    )
    customer_feedback = models.TextField(blank=True)
    driver_tip = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Estimated times
    estimated_pickup_time = models.DateTimeField(null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Delivery Request"
        verbose_name_plural = "Delivery Requests"

    def __str__(self):
        return f"{self.request_number} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            import random
            import string
            self.request_number = 'DR' + ''.join(random.choices(string.digits, k=8))
        
        # Calculate driver commission (e.g., 80% of delivery fee)
        if not self.driver_commission:
            self.driver_commission = self.delivery_fee * 0.80
            self.platform_fee = self.delivery_fee * 0.20
        
        super().save(*args, **kwargs)

    def assign_to_driver(self, driver):
        """Assign delivery to a specific driver"""
        self.driver = driver
        self.status = 'assigned'
        self.assigned_at = timezone.now()
        self.save()
        self.send_assignment_notification()

    def accept_by_driver(self):
        """Driver accepts the delivery"""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        self.send_acceptance_notification()

    def reject_by_driver(self, reason=''):
        """Driver rejects the delivery"""
        self.status = 'rejected'
        self.delivery_notes = reason
        self.save()
        if self.driver:
            self.driver.increment_rejected_orders()
        self.find_next_available_driver()

    def mark_picked_up(self):
        """Mark as picked up"""
        self.status = 'picked_up'
        self.picked_up_at = timezone.now()
        self.save()
        self.send_pickup_notification()

    def mark_delivered(self, proof_photo=None, signature=None):
        """Mark as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        if proof_photo:
            self.proof_photo = proof_photo
        if signature:
            self.customer_signature = signature
        self.save()
        
        # Update driver stats
        if self.driver:
            self.driver.completed_deliveries += 1
            self.driver.save()
        
        # Update order status if applicable
        if self.order:
            self.order.status = self.order.DELIVERED
            self.order.save()
        
        self.send_delivery_notification()

    def send_assignment_notification(self):
        """Notify driver about new delivery assignment"""
        # This would integrate with push notification service
        logger.info(f"Delivery {self.request_number} assigned to driver {self.driver.user.username}")

    def send_acceptance_notification(self):
        """Notify customer that driver accepted"""
        logger.info(f"Delivery {self.request_number} accepted by driver")

    def send_pickup_notification(self):
        """Notify customer that order is picked up"""
        logger.info(f"Delivery {self.request_number} picked up")

    def send_delivery_notification(self):
        """Notify customer that order is delivered"""
        logger.info(f"Delivery {self.request_number} delivered")

    def find_next_available_driver(self):
        """Find and assign next available driver"""
        # Logic to find nearby available drivers
        # This would be implemented in a service/view
        pass


class DriverRating(models.Model):
    """Ratings for drivers"""
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='ratings')
    delivery_request = models.OneToOneField(DeliveryRequest, on_delete=models.CASCADE, related_name='driver_rating')
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE)
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    
    # Rating Categories
    punctuality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    professionalism = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    care_of_items = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.driver.user.username} - {self.rating} stars"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update driver's average rating
        self.driver.average_rating = self.driver.ratings.aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating'] or 0
        self.driver.save()
