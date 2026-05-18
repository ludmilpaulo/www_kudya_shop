from rest_framework import serializers
from .models import PaymentProvider, Payment


class PaymentProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProvider
        fields = ['id', 'provider', 'country', 'active']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'service_type', 'object_id', 'amount', 'currency',
            'method', 'status', 'provider_reference', 'created_at',
        ]
        read_only_fields = ['status', 'provider_reference', 'created_at']
