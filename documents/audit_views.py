# documents/audit_views.py
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import Document

def generate_audit_report(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return HttpResponse("Document not found", status=404)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="audit_report_{document_id}.pdf"'

    p = canvas.Canvas(response)
    y = 800

    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, f"Audit Report for: {document.title}")
    y -= 40

    p.setFont("Helvetica", 12)

    for signature in document.signatures.all():
        signer = signature.signer.get_full_name() or signature.signer.username
        p.drawString(50, y, f"Signer: {signer}")
        y -= 20
        p.drawString(50, y, f"Signed at: {signature.signed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 20
        p.drawString(50, y, f"IP Address: {signature.ip_address or 'Unknown'}")
        y -= 20
        p.drawString(50, y, f"Device: {signature.user_agent[:80]}...")  # trim user agent string
        y -= 40

        if y < 100:
            p.showPage()
            y = 800

    p.save()
    return response
