import random
from datetime import timedelta
from django.utils import timezone
# documents/models.py
from django.db import models
from django.conf import settings
from .validators import validate_verification_file

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_signed = models.BooleanField(default=False)
    signed_file = models.FileField(upload_to='signed_documents/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Signature(models.Model):
    document = models.ForeignKey(Document, related_name='signatures', on_delete=models.CASCADE)
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signature_image = models.ImageField(upload_to='signatures/')
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)

    def __str__(self):
        return f"Signature by {self.signer.username} on {self.document.title}"


class OTP(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.created_at > timezone.now() - timedelta(minutes=10)  # 10 minutes valid

    @staticmethod
    def generate_otp(email):
        code = ''.join(random.choices('0123456789', k=6))
        otp = OTP.objects.create(email=email, code=code)
        return otp


import uuid

class SignatureInvite(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    sent_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ add this
    signed = models.BooleanField(default=False)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"Invite to {self.email} for {self.document.title}"


class VerificationDocument(models.Model):
    SUBJECT_TYPES = [
        ('user', 'User'),
        ('doctor_profile', 'Doctor Profile'),
        ('service_provider', 'Service Provider'),
        ('host', 'Host'),
        ('landlord', 'Landlord'),
        ('property_agent', 'Property Agent'),
        ('merchant', 'Merchant'),
        ('driver', 'Driver'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification_documents',
    )
    subject_type = models.CharField(max_length=40, choices=SUBJECT_TYPES, db_index=True)
    subject_id = models.PositiveIntegerField(db_index=True)
    document_type = models.CharField(max_length=80, db_index=True)
    file = models.FileField(
        upload_to='verification_documents/',
        validators=[validate_verification_file],
    )
    country = models.ForeignKey(
        'services.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_documents',
    )
    city = models.ForeignKey(
        'kudya_platform.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_documents',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verification_documents',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject_type', 'subject_id', 'document_type']),
        ]

    def __str__(self):
        return f'{self.subject_type}:{self.subject_id} {self.document_type}'

        
