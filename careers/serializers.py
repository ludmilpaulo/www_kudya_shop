from rest_framework import serializers
from .models import Career, JobApplication


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = ["id", "title", "description"]


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ["id", "career", "full_name", "email", "resume"]
