import io
import os
from PIL import Image
import fitz  # PyMuPDF
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from documents.models import Document, Signature


def embed_signature_into_pdf(
    document: Document,
    signature: Signature,
    x: float,
    y: float,
    page_number: int,
    render_width: float,
    render_height: float,
) -> None:
    signed_file_path = getattr(document.signed_file, 'path', None)
    base_path = signed_file_path if signed_file_path and os.path.exists(signed_file_path) else document.file.path

    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Base PDF not found: {base_path}")

    base_name = os.path.splitext(os.path.basename(base_path))[0]
    if '-signed-' in base_name:
        base_name = base_name.split('-signed-')[0]

    pdf_doc = fitz.open(base_path)
    page_index = max(0, min(len(pdf_doc) - 1, page_number - 1))
    page = pdf_doc[page_index]

    page_width_pt = page.rect.width
    page_height_pt = page.rect.height

    # Scale from rendered screen px to PDF pt
    x_pt = (x / render_width) * page_width_pt
    y_pt = (y / render_height) * page_height_pt
    sig_width_pt = (200 / render_width) * page_width_pt
    sig_height_pt = (100 / render_height) * page_height_pt

    img = Image.open(signature.signature_image.path)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()

    rect = fitz.Rect(x_pt, y_pt, x_pt + sig_width_pt, y_pt + sig_height_pt)
    page.insert_image(rect, stream=img_bytes)

    signer_name = signature.signer.get_full_name() or signature.signer.username
    signed_at = signature.signed_at.strftime("%Y-%m-%d %H:%M")
    page.insert_text(
        fitz.Point(x_pt, y_pt + sig_height_pt + 10),
        f"Signed by {signer_name} on {signed_at}",
        fontsize=10,
        color=(0, 0, 0)
    )

    signed_dir = os.path.join(settings.MEDIA_ROOT, 'signed_documents')
    os.makedirs(signed_dir, exist_ok=True)
    signed_filename = f"{base_name}-signed-{get_random_string(8)}.pdf"
    signed_path = os.path.join(signed_dir, signed_filename)

    pdf_doc.save(signed_path)
    pdf_doc.close()

    with open(signed_path, 'rb') as f:
        document.signed_file.save(signed_filename, ContentFile(f.read()), save=True)
