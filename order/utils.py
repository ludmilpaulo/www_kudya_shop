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
