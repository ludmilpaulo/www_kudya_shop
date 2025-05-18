from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from .models import SignatureInvite, Document
from .serializers import SignatureInviteSerializer
import uuid


from .models import SignatureInvite, Document
from .serializers import SignatureInviteSerializer
import uuid


class SignatureInviteViewSet(viewsets.ModelViewSet):
    queryset = SignatureInvite.objects.all()
    serializer_class = SignatureInviteSerializer
    permission_classes = [AllowAny]  # 🔓 Allows unauthenticated send, but we still check user_id manually

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        document_id = request.data.get('documentId')
        user_id = request.data.get('user_id')

        if not email or not document_id or not user_id:
            return Response({'detail': 'Missing fields.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({'detail': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid user.'}, status=status.HTTP_403_FORBIDDEN)

        # Generate secure token
        token = str(uuid.uuid4())

        invite = SignatureInvite.objects.create(
            document=document,
            email=email,
            token=token
        )

        serializer = self.get_serializer(invite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    


