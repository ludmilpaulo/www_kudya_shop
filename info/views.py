from rest_framework import generics
from .models import Image, Carousel, AboutUs, Why_Choose_Us, Team, Contact
from .serializers import ImageSerializer, CarouselSerializer, AboutUsSerializer, WhyChooseUsSerializer, TeamSerializer, ContactSerializer

# ListCreateAPIView for creating and listing all instances
class ImageListCreateAPIView(generics.ListCreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class CarouselListCreateAPIView(generics.ListCreateAPIView):
    queryset = Carousel.objects.all()
    serializer_class = CarouselSerializer

class AboutUsListCreateAPIView(generics.ListCreateAPIView):
    queryset = AboutUs.objects.all()
    serializer_class = AboutUsSerializer

class WhyChooseUsListCreateAPIView(generics.ListCreateAPIView):
    queryset = Why_Choose_Us.objects.all()
    serializer_class = WhyChooseUsSerializer

class TeamListCreateAPIView(generics.ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class ContactListCreateAPIView(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

# RetrieveUpdateDestroyAPIView for retrieving, updating and deleting a single instance
class ImageRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class CarouselRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Carousel.objects.all()
    serializer_class = CarouselSerializer

class AboutUsRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AboutUs.objects.all()
    serializer_class = AboutUsSerializer

class WhyChooseUsRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Why_Choose_Us.objects.all()
    serializer_class = WhyChooseUsSerializer

class TeamRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class ContactRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
  