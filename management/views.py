from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse

from order.models import Order
from order.serializers import OrderSerializer

from .serializers import RestaurantUserSerializer
from datetime import timedelta
from django.utils import timezone


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=False, methods=['get'], url_path='weekly-orders/(?P<restaurant_id>[^/.]+)')
    def filter_orders_weekly(self, request, restaurant_id=None):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        orders = Order.objects.filter(restaurant_id=restaurant_id, created_at__gte=week_ago)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='monthly-orders/(?P<restaurant_id>[^/.]+)')
    def filter_orders_monthly(self, request, restaurant_id=None):
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        orders = Order.objects.filter(restaurant_id=restaurant_id, created_at__gte=month_ago)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='invoice')
    def generate_pdf_invoice(self, request, pk=None):
        order = self.get_object()
        pdf_path, pdf_content = order.generate_invoice_pdf()
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
        return response

class RestaurantUserViewSet(viewsets.ModelViewSet):
    queryset = RestaurantUser.objects.all()
    serializer_class = RestaurantUserSerializer

    @action(detail=True, methods=['get'], url_path='user-invoice/(?P<restaurant_id>[^/.]+)/(?P<period>[^/.]+)')
    def generate_user_invoice(self, request, pk=None, restaurant_id=None, period=None):
        user = self.get_object()
        restaurant = Restaurant.objects.get(id=restaurant_id)
        association = RestaurantUser.objects.get(user=user, restaurant=restaurant)
        if period == 'weekly':
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            orders = Order.objects.filter(restaurant=restaurant, created_at__gte=week_ago)
        elif period == 'monthly':
            today = timezone.now().date()
            month_ago = today - timedelta(days=30)
            orders = Order.objects.filter(restaurant=restaurant, created_at__gte=month_ago)
        pdf_path, pdf_content = association.generate_user_invoice(orders)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="user_invoice_{user.id}_{period}.pdf"'
        return response
