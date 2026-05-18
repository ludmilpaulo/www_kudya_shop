from rest_framework import serializers
from .models import Wallet, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'amount', 'currency', 'status',
            'reference', 'description', 'service_type', 'created_at',
        ]


class WalletSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id', 'owner_type', 'currency', 'available_balance',
            'pending_balance', 'transactions',
        ]
