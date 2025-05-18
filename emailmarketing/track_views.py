from django.http import HttpResponse
from django.utils.timezone import now
from .models import EmailLog

def open_tracking_pixel(request, campaign_id, recipient):
    EmailLog.objects.filter(
        campaign_id=campaign_id,
        recipient=recipient
    ).update(opened=True, status='opened', timestamp=now())

    # Return a 1x1 transparent GIF
    pixel = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B'
    )
    return HttpResponse(pixel, content_type='image/gif')
