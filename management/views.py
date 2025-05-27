from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from drivers.models import Driver
from drivers.serializers import DriverSerializer
from management.models import Partner
from management.serializers import PartnerSerializer
from order.models import Order
from order.serializers import OrderSerializer
from stores.models import Store
from stores.serializers import StoreSerializer


class storeViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["get"])
    def earnings(self, request, pk=None):
        store = get_object_or_404(Store, pk=pk)
        orders = Order.objects.filter(store=store)
        total_earnings = sum(order.total for order in orders)
        return Response(
            {
                "total_earnings": total_earnings,
                "orders": OrderSerializer(orders, many=True).data,
            }
        )


class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["get"])
    def earnings(self, request, pk=None):
        partner = get_object_or_404(Partner, pk=pk)
        earnings = partner.earnings
        return Response({"total_earnings": earnings})


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["get"])
    def earnings(self, request, pk=None):
        driver = get_object_or_404(Driver, pk=pk)
        total_earnings = sum(
            order.calculate_driver_commission()
            for order in Order.objects.filter(driver=driver)
        )
        return Response({"total_earnings": total_earnings})
