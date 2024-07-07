from django.core.mail import EmailMessage
from django.conf import settings

def send_notification(mail_subject, message, to_email):
    from_email = settings.DEFAULT_FROM_EMAIL
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()
