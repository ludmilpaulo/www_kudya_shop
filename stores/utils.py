import logging
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from weasyprint import HTML

logger = logging.getLogger(__name__)


def send_notification(mail_subject, message, to_email):
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        mail = EmailMessage(mail_subject, message, from_email, [to_email])
        mail.content_subtype = "html"
        mail.send()
    except Exception as e:
        logger.error(f"Error sending email: {e}")


def generate_invoice(context):
    html_string = render_to_string("invoice_template.html", context)
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    return pdf
