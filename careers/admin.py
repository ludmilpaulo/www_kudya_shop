from django.contrib import admin
from .models import Career, JobApplication

@admin.register(Career)
class OrderAdmin(admin.ModelAdmin):
    pass
@admin.register(JobApplication)
class OrderDetailsAdmin(admin.ModelAdmin):
    pass