import uuid
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction as db_transaction

from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user, is_active=True)

    @action(detail=False, methods=['get'])
    def me(self, request):
        currency = request.query_params.get('currency', 'ZAR')
        wallet, _ = Wallet.objects.get_or_create(
            owner_type='customer',
            owner_id=request.user.id,
            currency=currency,
            defaults={'user': request.user},
        )
        if not wallet.user_id:
            wallet.user = request.user
            wallet.save(update_fields=['user'])
        return Response(WalletSerializer(wallet).data)

    @action(detail=False, methods=['post'])
    def top_up(self, request):
        amount = Decimal(str(request.data.get('amount', 0)))
        currency = request.data.get('currency', 'ZAR')
        if amount <= 0:
            return Response({'amount': 'Must be positive.'}, status=status.HTTP_400_BAD_REQUEST)
        wallet, _ = Wallet.objects.get_or_create(
            owner_type='customer',
            owner_id=request.user.id,
            currency=currency,
            defaults={'user': request.user},
        )
        with db_transaction.atomic():
            wallet.available_balance += amount
            wallet.save(update_fields=['available_balance'])
            tx = Transaction.objects.create(
                wallet=wallet,
                transaction_type='top_up',
                amount=amount,
                currency=currency,
                status='completed',
                reference=f'TOP-{uuid.uuid4().hex[:12].upper()}',
                description='Wallet top up',
            )
        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def history(self, request):
        wallets = self.get_queryset()
        txs = Transaction.objects.filter(wallet__in=wallets).order_by('-created_at')[:100]
        return Response(TransactionSerializer(txs, many=True).data)
