from rest_framework.permissions import AllowAny
import io
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document, Signature
from .serializers import DocumentSerializer, SignatureSerializer


from django.contrib.auth.models import User

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        user_id = request.data.get("uploaded_by")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Construct data manually without deepcopy
        data = {
            "title": request.data.get("title"),
            "uploaded_by": user.id,
        }

        files = {"file": request.FILES.get("file")}

        serializer = self.get_serializer(data={**data, **files})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        print("🚨 Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



