from rest_framework import serializers
from .models import Career, JobApplication

class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = '__all__'


class JobApplicationSerializer(serializers.ModelSerializer):
    career = CareerSerializer(read_only=True)
    language = serializers.ChoiceField(choices=[('en', 'English'), ('pt', 'Português')], default='en')
    career_id = serializers.PrimaryKeyRelatedField(
        queryset=Career.objects.all(),
        source='career',
        write_only=True
    )
    resume = serializers.FileField()

    class Meta:
        model = JobApplication
        fields = [
            'id',
            'career',
            'career_id',
            'full_name',
            'email',
            'resume',
            'language',
            'cover_letter',
            'submitted_at',
            'status',
        ]
        read_only_fields = ['submitted_at']  # ✅ removed 'status'
