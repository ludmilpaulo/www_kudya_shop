from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from documents.models import Document
from django.core.files.base import ContentFile

@api_view(['POST'])
@parser_classes([MultiPartParser])
def save_signed_pdf(request):
    document_id = request.data.get('document_id')
    user_id = request.data.get('user_id')  # optional for audit logging
    file = request.FILES.get('file')

    if not document_id or not file:
        return Response({'error': 'Missing required fields'}, status=400)

    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=404)

    document.signed_file.save(f"signed_{file.name}", file, save=True)
    document.is_signed = True
    document.save()

    return Response({'success': True, 'signed_file': document.signed_file.url})
