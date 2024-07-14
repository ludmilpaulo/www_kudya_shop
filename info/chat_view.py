# views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from order.models import Order

from .models import  ChatMessage
from .serializers import ChatMessageSerializer

from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(['POST'])
def send_chat_message(request):
    user_id = request.data.get('user_id')
    user = User.objects.get(pk=user_id)
    order_id = request.data.get('order_id')
    message = request.data.get('message')
    order = get_object_or_404(Order, id=order_id)

    if order.status != Order.VERIFIED:
        return Response({'error': 'Order is not on the way'}, status=status.HTTP_400_BAD_REQUEST)

    chat_message = ChatMessage.objects.create(
        order=order,
        sender=user,
        message=message
    )
    serializer = ChatMessageSerializer(chat_message)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def get_order_chat(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    messages = ChatMessage.objects.filter(order=order).order_by('timestamp')
    serializer = ChatMessageSerializer(messages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
