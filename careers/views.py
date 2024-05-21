from rest_framework import generics
from .models import Career, JobApplication
from .serializers import CareerSerializer, JobApplicationSerializer

class CareerListAPIView(generics.ListAPIView):
    queryset = Career.objects.all()
    serializer_class = CareerSerializer

class JobApplicationCreateAPIView(generics.CreateAPIView):
    serializer_class = JobApplicationSerializer