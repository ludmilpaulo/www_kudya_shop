from rest_framework import serializers
from .models import ChatMessage, Image, Carousel, AboutUs, Why_Choose_Us, Team, Contact


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["image"]


class CarouselSerializer(serializers.ModelSerializer):
    image = ImageSerializer(many=True)

    class Meta:
        model = Carousel
        fields = ["id", "image", "title", "sub_title"]


class AboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = "__all__"


class WhyChooseUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Why_Choose_Us
        fields = "__all__"


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"




class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'order', 'sender', 'sender_username', 'message', 'timestamp']
