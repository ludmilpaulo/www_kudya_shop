from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Wallet(models.Model):
    OWNER_TYPES = [
        ('customer', 'Customer'),
        ('driver', 'Driver'),
        ('merchant', 'Merchant'),
        ('doctor', 'Doctor'),
        ('service_provider', 'Service Provider'),
        ('host', 'Host'),
        ('landlord', 'Landlord'),
        ('agent', 'Property Agent'),
        ('business', 'Business Account'),
        ('platform', 'Platform'),
    ]

    owner_type = models.CharField(max_length=20, choices=OWNER_TYPES, db_index=True)
    owner_id = models.PositiveIntegerField(db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets', null=True, blank=True)
    currency = models.CharField(max_length=3, default='ZAR')
    available_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    pending_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner_type', 'owner_id', 'currency')

    def __str__(self):
        return f'{self.owner_type}:{self.owner_id} ({self.currency})'


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('top_up', 'Top Up'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('earning', 'Earning'),
        ('payout', 'Payout'),
        ('transfer', 'Transfer'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    service_type = models.CharField(max_length=50, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
