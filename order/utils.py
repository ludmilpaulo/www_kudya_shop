from io import BytesIO
from django.template.loader import get_template
from weasyprint import HTML
from django.core.files.base import ContentFile

def generate_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = HTML(string=html).write_pdf(result)
    return ContentFile(result.getvalue(), 'invoice.pdf')



from django.template.loader import render_to_string
from django.conf import settings
import os

def generate_invoice(order):
    context = {
        'order_id': order.id,
        'customer_name': order.customer.user.get_full_name(),
        'address': order.address,
        'order_details': [
            {
                'meal_name': detail.meal.name,
                'quantity': detail.quantity,
                'sub_total': detail.sub_total,
            } for detail in order.order_details.all()
        ],
        'order_total': order.total,
    }
    html_string = render_to_string('email_templates/order_invoice.html', context)
    invoice_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(invoice_dir, exist_ok=True)
    pdf_file_path = os.path.join(invoice_dir, f'order_{order.id}.pdf')

    HTML(string=html_string).write_pdf(pdf_file_path)
    return pdf_file_path
