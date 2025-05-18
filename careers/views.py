from django.core.mail import EmailMessage
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Career, JobApplication
from .serializers import CareerSerializer, JobApplicationSerializer
from django.template.loader import render_to_string
from rest_framework import viewsets, permissions



class CareerViewSet(viewsets.ModelViewSet):
    queryset = Career.objects.all().order_by('-created_at')
    serializer_class = CareerSerializer
    permission_classes = [permissions.AllowAny] 
