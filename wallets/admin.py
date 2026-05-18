from django.contrib import admin
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['owner_type', 'owner_id', 'currency', 'available_balance', 'pending_balance']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'wallet', 'transaction_type', 'amount', 'status', 'created_at']
    list_filter = ['transaction_type', 'status']
