from rest_framework import serializers
from django.contrib.auth.models import User
from .models import EmailCampaign, EmailLog

class UserEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']



class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = ['recipient', 'status', 'timestamp', 'opened']

class EmailCampaignSerializer(serializers.ModelSerializer):
    logs = EmailLogSerializer(many=True, read_only=True)

    class Meta:
        model = EmailCampaign
        fields = ['id', 'title', 'subject', 'body_html', 'recipient_list', 'status', 'created_at', 'logs']
