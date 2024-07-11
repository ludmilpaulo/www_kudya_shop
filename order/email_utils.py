from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_order_email(to_email, order, pdf_path, pdf_content, is_restaurant=False):
    context = {
        "customer_name": order.customer.user.get_full_name(),
        "order_status": order.get_status_display(),
        "order_id": order.id,
        "order_total": order.total,
        "address": order.address,
        "order_details": order.order_details.all(),
        "secret_pin": order.secret_pin,
    }
    subject = "Novo Pedido" if is_restaurant else "Pedido Recebido"
    message = render_to_string("email_templates/order_confirmation.html", context)

    email_message = EmailMessage(
        subject, message, settings.DEFAULT_FROM_EMAIL, [to_email]
    )
    email_message.attach(f"order_{order.id}.pdf", pdf_content, "application/pdf")
    email_message.content_subtype = "html"

    try:
        email_message.send()
        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
        raise e
