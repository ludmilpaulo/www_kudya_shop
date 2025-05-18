from django.contrib import admin
from .models import Career, JobApplication

@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'created_at')
    search_fields = ('title', 'location')

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'career', 'submitted_at')
    search_fields = ('full_name', 'email', 'career__title')
