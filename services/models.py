from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# ==================== LOCATION MODELS ====================
class Country(models.Model):
    """Country model for multi-region support"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)  # ISO country code
    flag_icon = models.CharField(max_length=10, blank=True)  # emoji or icon
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return self.name


class Province(models.Model):
    """Province/State model for region-specific services"""
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='provinces')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('country', 'name')
        ordering = ['country', 'name']

    def __str__(self):
        return f"{self.name}, {self.country.name}"


# ==================== SERVICE MODELS ====================
class ServiceCategory(models.Model):
    """Categories for services like Health, Education, Delivery, etc."""
    CATEGORY_TYPES = [
        ('health', 'Health & Medical'),
        ('education', 'Education & Training'),
        ('beauty', 'Beauty & Wellness'),
        ('home', 'Home Services'),
        ('legal', 'Legal Services'),
        ('transport', 'Transport & Delivery'),
        ('tech', 'Technology & IT'),
        ('other', 'Other Services'),
    ]

    name = models.CharField(max_length=200, unique=True)
    name_pt = models.CharField(max_length=200, blank=True, verbose_name="Nome em Português")
    slug = models.SlugField(max_length=200, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, default='other')
    icon = models.CharField(max_length=50, blank=True, default='briefcase')  # FontAwesome icon
    image = models.ImageField(upload_to='service_categories/', blank=True)
    description = models.TextField(blank=True)
    description_pt = models.TextField(blank=True, verbose_name="Descrição em Português")
    requires_license = models.BooleanField(default=False)  # e.g., doctors, lawyers
    requires_region_verification = models.BooleanField(default=False)  # for regulated professions
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Service(models.Model):
    """Services offered by parceiros (doctors, plumbers, tutors, etc.)"""
    DELIVERY_TYPES = [
        ('in_person', 'In Person (at service location)'),
        ('at_customer', 'At Customer Location'),
        ('online', 'Online/Virtual'),
        ('hybrid', 'Hybrid (Any)'),
    ]

    # Basic Information
    parceiro = models.ForeignKey('stores.Store', on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=300)
    title_pt = models.CharField(max_length=300, blank=True, verbose_name="Título em Português")
    description = models.TextField()
    description_pt = models.TextField(blank=True, verbose_name="Descrição em Português")
    
    # Pricing & Duration
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AOA')
    duration_minutes = models.IntegerField(default=90, help_text="Duration in minutes")
    
    # Delivery & Location
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPES, default='in_person')
    service_location = models.CharField(max_length=500, blank=True, help_text="Address if in-person")
    service_radius_km = models.IntegerField(default=0, help_text="Service radius for at_customer delivery")
    
    # Region Restrictions (for regulated services like doctors)
    allowed_countries = models.ManyToManyField(Country, blank=True, related_name='allowed_services')
    allowed_provinces = models.ManyToManyField(Province, blank=True, related_name='allowed_services')
    
    # Media
    image = models.ImageField(upload_to='service_images/', blank=True)
    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo URL")
    
    # Status & Features
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    instant_booking = models.BooleanField(default=True, help_text="Allow instant booking without approval")
    requires_approval = models.BooleanField(default=False, help_text="Parceiro must approve booking")
    
    # SEO & Metadata
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return f"{self.title} - {self.parceiro.name}"

    @property
    def average_rating(self):
        reviews = self.service_reviews.all()
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0

    @property
    def total_bookings(self):
        return self.bookings.filter(status='completed').count()

    def is_available_in_region(self, country, province=None):
        """Check if service is available in a specific region"""
        if not self.allowed_countries.exists():
            return True  # No restrictions
        
        if country not in self.allowed_countries.all():
            return False
        
        if province and self.allowed_provinces.exists():
            return province in self.allowed_provinces.all()
        
        return True


class ServiceAvailability(models.Model):
    """Service availability schedule - weekly recurring or specific dates"""
    WEEKDAYS = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='availability_slots')
    
    # Recurring Schedule
    is_recurring = models.BooleanField(default=True)
    day_of_week = models.IntegerField(choices=WEEKDAYS, null=True, blank=True)
    
    # Specific Date (for one-time availability)
    specific_date = models.DateField(null=True, blank=True)
    
    # Time Slots
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name_plural = "Service Availabilities"

    def __str__(self):
        if self.is_recurring:
            return f"{self.get_day_of_week_display()} {self.start_time} - {self.end_time}"
        return f"{self.specific_date} {self.start_time} - {self.end_time}"

    def generate_time_slots(self, date, slot_duration_minutes):
        """Generate available time slots for a specific date"""
        slots = []
        current_time = datetime.combine(date, self.start_time)
        end_datetime = datetime.combine(date, self.end_time)
        
        while current_time + timedelta(minutes=slot_duration_minutes) <= end_datetime:
            slots.append(current_time.time())
            current_time += timedelta(minutes=slot_duration_minutes)
        
        return slots


class BlackoutDate(models.Model):
    """Days when service provider is unavailable (vacation, holidays, etc.)"""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='blackout_dates')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.service.title} - {self.start_date} to {self.end_date}"


class Booking(models.Model):
    """Service bookings by customers"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled_customer', 'Cancelled by Customer'),
        ('cancelled_provider', 'Cancelled by Provider'),
        ('no_show', 'No Show'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]

    # Core Information
    booking_number = models.CharField(max_length=20, unique=True, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='service_bookings')
    
    # Booking DateTime
    booking_date = models.DateField()
    booking_time = models.TimeField()
    duration_minutes = models.IntegerField()
    
    # Location (if at customer location)
    customer_location = models.CharField(max_length=500, blank=True)
    customer_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    customer_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Status & Payment
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    provider_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Communication
    customer_notes = models.TextField(blank=True)
    provider_notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Proof & Verification
    completion_photo = models.ImageField(upload_to='booking_proofs/', blank=True)
    customer_signature = models.ImageField(upload_to='booking_signatures/', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Reminders
    reminder_24h_sent = models.BooleanField(default=False)
    reminder_2h_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-booking_date', '-booking_time']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"{self.booking_number} - {self.service.title}"

    def save(self, *args, **kwargs):
        if not self.booking_number:
            # Generate unique booking number
            import random
            import string
            self.booking_number = 'BK' + ''.join(random.choices(string.digits, k=8))
        
        # Calculate platform fee and provider earnings
        if not self.platform_fee:
            self.platform_fee = self.price * 0.15  # 15% platform fee
            self.provider_earnings = self.price - self.platform_fee
        
        super().save(*args, **kwargs)

    def send_confirmation_email(self):
        """Send booking confirmation email"""
        context = {
            'booking': self,
            'customer': self.customer,
            'service': self.service,
        }
        subject = f"Booking Confirmation - {self.booking_number}"
        message = render_to_string('emails/booking_confirmation.html', context)
        
        try:
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.customer.user.email, self.service.parceiro.user.email],
            )
            email.content_subtype = 'html'
            email.send()
            logger.info(f"Confirmation email sent for booking {self.booking_number}")
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")

    def check_time_conflict(self):
        """Check if booking time conflicts with existing bookings"""
        start_datetime = datetime.combine(self.booking_date, self.booking_time)
        end_datetime = start_datetime + timedelta(minutes=self.duration_minutes)
        
        conflicting_bookings = Booking.objects.filter(
            service=self.service,
            booking_date=self.booking_date,
            status__in=['pending', 'confirmed', 'in_progress']
        ).exclude(id=self.id)
        
        for booking in conflicting_bookings:
            booking_start = datetime.combine(booking.booking_date, booking.booking_time)
            booking_end = booking_start + timedelta(minutes=booking.duration_minutes)
            
            # Check for overlap
            if start_datetime < booking_end and end_datetime > booking_start:
                return True  # Conflict found
        
        return False  # No conflict


class ServiceReview(models.Model):
    """Reviews for services"""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='service_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Provider Response
    provider_response = models.TextField(blank=True)
    provider_response_date = models.DateTimeField(null=True, blank=True)
    
    # Helpful votes
    helpful_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service Review"
        verbose_name_plural = "Service Reviews"

    def __str__(self):
        return f"{self.service.title} - {self.rating} stars"


# ==================== KYC & VERIFICATION MODELS ====================
class ParceirKYC(models.Model):
    """KYC verification for parceiros"""
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmit', 'Resubmit Required'),
    ]

    DOCUMENT_TYPES = [
        ('id_card', 'National ID Card'),
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
        ('business_license', 'Business License'),
        ('professional_license', 'Professional License'),
        ('tax_certificate', 'Tax Certificate'),
    ]

    parceiro = models.OneToOneField('stores.Store', on_delete=models.CASCADE, related_name='kyc')
    
    # Personal Information
    full_legal_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    
    # Documents
    id_document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES, default='id_card')
    id_document_number = models.CharField(max_length=100)
    id_document_front = models.ImageField(upload_to='kyc/documents/')
    id_document_back = models.ImageField(upload_to='kyc/documents/', blank=True)
    
    # Additional Documents
    professional_license = models.FileField(upload_to='kyc/licenses/', blank=True)
    business_license = models.FileField(upload_to='kyc/licenses/', blank=True)
    tax_certificate = models.FileField(upload_to='kyc/tax/', blank=True)
    
    # Selfie Verification
    selfie_photo = models.ImageField(upload_to='kyc/selfies/', blank=True)
    
    # Bank Details (for payouts)
    bank_name = models.CharField(max_length=200)
    account_holder_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100)
    iban = models.CharField(max_length=100, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)
    
    # Verification Status
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    rejection_reason = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Verified Badge
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_kycs')
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parceiro KYC"
        verbose_name_plural = "Parceiros KYC"

    def __str__(self):
        return f"{self.parceiro.name} - {self.get_status_display()}"

    def approve(self, admin_user):
        """Approve KYC verification"""
        self.status = 'approved'
        self.is_verified = True
        self.verified_at = timezone.now()
        self.verified_by = admin_user
        self.save()
        self.send_approval_email()

    def reject(self, reason):
        """Reject KYC verification"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.is_verified = False
        self.save()
        self.send_rejection_email()

    def send_approval_email(self):
        context = {'kyc': self, 'parceiro': self.parceiro}
        subject = "KYC Verification Approved"
        message = render_to_string('emails/kyc_approved.html', context)
        
        try:
            email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [self.parceiro.user.email])
            email.content_subtype = 'html'
            email.send()
        except Exception as e:
            logger.error(f"Error sending KYC approval email: {e}")

    def send_rejection_email(self):
        context = {'kyc': self, 'parceiro': self.parceiro}
        subject = "KYC Verification Rejected"
        message = render_to_string('emails/kyc_rejected.html', context)
        
        try:
            email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [self.parceiro.user.email])
            email.content_subtype = 'html'
            email.send()
        except Exception as e:
            logger.error(f"Error sending KYC rejection email: {e}")


# ==================== PAYOUT MODELS ====================
class PayoutRequest(models.Model):
    """Payout requests from parceiros"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    parceiro = models.ForeignKey('stores.Store', on_delete=models.CASCADE, related_name='payout_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AOA')
    
    # Bank Details (from KYC or custom)
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=200)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    
    # Proof of Payment
    proof_of_payment = models.FileField(upload_to='payout_proofs/', blank=True)
    transaction_reference = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']
        verbose_name = "Payout Request"
        verbose_name_plural = "Payout Requests"

    def __str__(self):
        return f"{self.parceiro.name} - {self.amount} {self.currency}"


class ParceiroEarnings(models.Model):
    """Track earnings for parceiros from different sources"""
    EARNING_TYPES = [
        ('product_sale', 'Product Sale'),
        ('service_booking', 'Service Booking'),
        ('delivery_fee', 'Delivery Fee'),
    ]

    parceiro = models.ForeignKey('stores.Store', on_delete=models.CASCADE, related_name='earnings')
    earning_type = models.CharField(max_length=20, choices=EARNING_TYPES)
    
    # Reference to source
    order = models.ForeignKey('order.Order', on_delete=models.CASCADE, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    
    # Amounts
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AOA')
    
    # Payout Status
    is_paid_out = models.BooleanField(default=False)
    payout_request = models.ForeignKey(PayoutRequest, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    earned_at = models.DateTimeField(auto_now_add=True)
    paid_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-earned_at']
        verbose_name = "Parceiro Earnings"
        verbose_name_plural = "Parceiro Earnings"

    def __str__(self):
        return f"{self.parceiro.name} - {self.net_amount} {self.currency}"
