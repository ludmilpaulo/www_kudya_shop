from django.template.loader import render_to_string, get_template
from weasyprint import HTML
import tempfile
from django.core.files.base import ContentFile
from io import BytesIO

import logging

logger = logging.getLogger(__name__)


def generate_invoice(order):
    logger.info(f"Generating invoice for order {order.id}")
    context = {
        "order_id": order.id,
        "customer_name": order.customer.user.get_full_name(),
        "address": order.address,
        "order_details": [
            {
                "meal_name": detail.meal.name,
                "quantity": detail.quantity,
                "sub_total": detail.sub_total,
            }
            for detail in order.order_details.all()
        ],
        "order_total": order.total,
    }
    html_string = render_to_string("email_templates/order_invoice.html", context)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        HTML(string=html_string).write_pdf(temp_pdf.name)
        temp_pdf.seek(0)
        pdf_content = temp_pdf.read()
    logger.info(f"Invoice generated for order {order.id}")
    return temp_pdf.name, pdf_content


def generate_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = HTML(string=html).write_pdf(result)
    return ContentFile(result.getvalue(), "invoice.pdf")
