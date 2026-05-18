from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import PaymentProvider, Payment
from .serializers import PaymentSerializer, PaymentProviderSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_methods(request):
    country = request.query_params.get('country', 'ZA')
    providers = PaymentProvider.objects.filter(country=country, active=True)
    return Response(PaymentProviderSerializer(providers, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    serializer = PaymentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


urlpatterns = [
    path('methods/', payment_methods, name='payment-methods'),
    path('', create_payment, name='payment-create'),
]
