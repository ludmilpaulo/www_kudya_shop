from django.db import models
from datetime import date, datetime, time
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from django.template.loader import render_to_string
import logging

User = get_user_model()

class StoreType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to="store_type_icons/", blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Store Type"
        verbose_name_plural = "Store Types"

    def __str__(self):
        return self.name


class StoreCategory(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    image = models.ImageField(upload_to="category/", blank=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Store Category"
        verbose_name_plural = "Store Categories"

    def __str__(self):
        return self.name


class Store(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="usuário", blank=True)
    store_type = models.ForeignKey(StoreType, on_delete=models.SET_NULL, null=True, related_name="stores")
    category = models.ForeignKey(StoreCategory, related_name="stores", on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=500)
    phone = models.CharField(max_length=500)
    address = models.CharField(max_length=500)
    logo = models.ImageField(upload_to="store_logos/")
    location = models.CharField(max_length=500, blank=True)
    license = models.FileField(upload_to="vendor/license", blank=True)
    banner = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name


