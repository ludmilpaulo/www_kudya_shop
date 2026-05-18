from django.contrib import admin
from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'category', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'category']
