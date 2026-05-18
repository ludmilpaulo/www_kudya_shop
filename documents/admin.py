from django.contrib import admin

from .models import VerificationDocument


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'subject_type',
        'subject_id',
        'document_type',
        'owner',
        'country',
        'city',
        'status',
        'reviewed_by',
        'created_at',
    ]
    list_filter = ['subject_type', 'document_type', 'status', 'country', 'city']
    search_fields = ['owner__email', 'document_type', 'subject_id']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at']
