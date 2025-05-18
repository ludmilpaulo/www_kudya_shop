from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.conf import settings
from .models import EmailCampaign, EmailLog
from .serializers import EmailCampaignSerializer, EmailLogSerializer

class EmailCampaignViewSet(viewsets.ModelViewSet):
    queryset = EmailCampaign.objects.all().order_by('-created_at')
    serializer_class = EmailCampaignSerializer
    
    @action(detail=False, methods=['get'])
    def user_emails(self, request):
        users = User.objects.exclude(email='').values_list('email', flat=True)
        return Response(list(users))

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        campaign = self.get_object()
        success = True

        for email in campaign.recipient_list:
            try:
                msg = EmailMultiAlternatives(
                    subject=campaign.subject,
                    body='',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                # Embed tracking pixel
                tracking_url = f"{request.build_absolute_uri('/email/open-tracking/')}{campaign.id}/{email}/"
                body_with_tracking = f"{campaign.body_html}<img src='{tracking_url}' width='1' height='1' alt=''/>"
                msg.attach_alternative(body_with_tracking, "text/html")
                msg.send()

                # Log success
                EmailLog.objects.create(campaign=campaign, recipient=email, status='sent')

            except Exception as e:
                success = False
                EmailLog.objects.create(campaign=campaign, recipient=email, status='failed')
                print(f"❌ Failed to send to {email}: {str(e)}")

        campaign.status = 'sent' if success else 'failed'
        campaign.save()

        return Response({'status': campaign.status})

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        campaign = self.get_object()
        logs = campaign.logs.all().order_by('-timestamp')
        serializer = EmailLogSerializer(logs, many=True)
        return Response(serializer.data)
