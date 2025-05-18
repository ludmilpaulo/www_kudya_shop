from django.db import models

class EmailCampaign(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    recipient_list = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('opened', 'Opened'),
    ]

    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='logs')
    recipient = models.EmailField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    timestamp = models.DateTimeField(auto_now_add=True)
    opened = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.recipient} - {self.status}"
