from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SupportTicket(models.Model):
    CATEGORIES = [
        ('payment', 'Failed Payment'),
        ('wrong_order', 'Wrong Order'),
        ('missing_item', 'Missing Item'),
        ('driver', 'Driver Behavior'),
        ('customer', 'Customer Behavior'),
        ('late_delivery', 'Late Delivery'),
        ('damaged_package', 'Damaged Package'),
        ('rental', 'Rental Issue'),
        ('refund', 'Refund Request'),
        ('safety', 'Safety Issue'),
        ('other', 'Other'),
    ]
    STATUS = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    PRIORITY = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    category = models.CharField(max_length=30, choices=CATEGORIES)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='open', db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
    )
    service_type = models.CharField(max_length=30, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
