from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from documents.models import Document, Signature
from documents.serializers import SignatureSerializer
from .pdf import embed_signature_into_pdf


class SignatureViewSet(viewsets.ModelViewSet):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        try:
            document_id = int(request.data.get("document"))
            user_id = int(request.data.get("user_id"))
            x = float(request.data.get("x", 100))
            y = float(request.data.get("y", 500))
            page_number = int(request.data.get("page_number", 1))
            render_width = float(request.data.get("render_width", 800))
            render_height = float(request.data.get("render_height", 1100))
        except (ValueError, TypeError):
            return Response({"detail": "Invalid input."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            document = Document.objects.get(id=document_id)
            user = User.objects.get(id=user_id)
        except Document.DoesNotExist:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        signature_image = request.FILES.get("signature_image")
        if not signature_image:
            return Response({"detail": "Signature image is required."}, status=status.HTTP_400_BAD_REQUEST)

        signature = Signature.objects.create(
            document=document,
            signer=user,
            signature_image=signature_image,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

        try:
            embed_signature_into_pdf(document, signature, x, y, page_number, render_width, render_height)
        except FileNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        document.is_signed = True
        document.save()

        serializer = self.get_serializer(signature)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
