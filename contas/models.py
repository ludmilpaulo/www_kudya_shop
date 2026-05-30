from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.dispatch import receiver


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('driver', 'Driver'),
        ('courier', 'Courier'),
        ('merchant', 'Merchant Owner'),
        ('restaurant', 'Restaurant Owner'),
        ('grocery_store_owner', 'Grocery Store Owner'),
        ('doctor', 'Doctor'),
        ('clinic_admin', 'Clinic Admin'),
        ('service_provider', 'Service Provider'),
        ('host', 'Host'),
        ('landlord', 'Landlord'),
        ('agent', 'Property Agent'),
        ('rental_partner', 'Rental Partner'),
        ('business_admin', 'Business Account Admin'),
        ('business_employee', 'Business Employee'),
        ('support', 'Support Agent'),
        ('country_admin', 'Country Admin'),
        ('city_admin', 'City Admin'),
        ('finance_admin', 'Finance Admin'),
        ('compliance_admin', 'Compliance Admin'),
        ('safety_admin', 'Safety Admin'),
        ('super_admin', 'Super Admin'),
    ]
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('pt', 'Portuguese'),
        ('fr', 'French'),
        ('es', 'Spanish'),
    ]

    is_customer = models.BooleanField(default=False)
    is_driver = models.BooleanField(default=False)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='customer', db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    preferred_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    country = models.ForeignKey(
        'services.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    city = models.ForeignKey(
        'kudya_platform.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    is_verified = models.BooleanField(default=False)

    ADMIN_ROLES = {
        'super_admin',
        'country_admin',
        'city_admin',
        'support',
        'finance_admin',
        'compliance_admin',
        'safety_admin',
    }

    def has_any_role(self, *roles):
        return self.is_superuser or self.role in set(roles)

    @property
    def is_platform_admin(self):
        return self.is_superuser or self.role in self.ADMIN_ROLES

    def __str__(self):
        return self.username


class SocialAccount(models.Model):
    PROVIDERS = [
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='social_accounts',
    )
    provider = models.CharField(max_length=20, choices=PROVIDERS, db_index=True)
    provider_user_id = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('provider', 'provider_user_id')]
        indexes = [
            models.Index(fields=['provider', 'provider_user_id']),
        ]

    def __str__(self):
        return f'{self.provider}:{self.provider_user_id}'


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
