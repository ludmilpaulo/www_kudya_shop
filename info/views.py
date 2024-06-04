from rest_framework import generics
from www_kudya_shop import settings
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


from rest_framework import generics
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Contact
from .serializers import ContactSerializer

class ContactListCreateAPIView(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        contact = Contact.objects.get(id=response.data['id'])
        self.send_confirmation_email(contact)
        return response

    def send_confirmation_email(self, contact):
        subject = 'Confirmação de contato'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = contact.email
        context = {
            'subject': contact.subject,
            'email': contact.email,
            'phone': contact.phone,
            'message': contact.message
        }
        html_content = render_to_string('emails/contact_confirmation.html', context)
        email = EmailMultiAlternatives(subject, None, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        email.send()
