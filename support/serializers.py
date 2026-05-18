from rest_framework import serializers
from .models import SupportTicket


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'category', 'subject', 'message', 'status', 'priority',
            'service_type', 'object_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SupportTicketAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'category', 'subject', 'message', 'status', 'priority',
            'assigned_to', 'service_type', 'object_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
