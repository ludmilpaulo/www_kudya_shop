from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SignatureInvite
from .serializers import SignatureInviteSerializer
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from .models import SignatureInvite, Document
from .serializers import SignatureInviteSerializer
import uuid

class SendInviteView(APIView):
    def post(self, request):
        email = request.data.get('email')
        document_id = request.data.get('documentId')
        user_id = request.data.get('user_id')

        if not email or not document_id or not user_id:
            return Response({"detail": "Missing fields."}, status=status.HTTP_400_BAD_REQUEST)

        document = get_object_or_404(Document, id=document_id)
        invited_by = get_object_or_404(User, id=user_id)

        token = str(uuid.uuid4())

        invite = SignatureInvite.objects.create(
            document=document,
            email=email,
            token=token,
            invited_by=invited_by
        )

        signing_url = f"{settings.FRONTEND_URL}/UserSign?token={token}"

        subject = "Action Required: Please Sign Document"
        context = {
            "document_title": document.title,
            "signing_url": signing_url,
            "support_email": dict(settings.ADMINS).get("Support Team", "support@maindodigital.com"),
        }

        html_content = render_to_string("emails/sign_invite_email.html", context)
        text_content = f"Please sign document here: {signing_url}"

        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return Response(SignatureInviteSerializer(invite, context={'request': request}).data, status=status.HTTP_201_CREATED)


class GetInviteByTokenView(APIView):
    def get(self, request, token):
        invite = get_object_or_404(SignatureInvite, token=token)
        serializer = SignatureInviteSerializer(invite, context={'request': request})
        return Response(serializer.data)

from django.core.mail import EmailMultiAlternatives
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SignatureInvite, Document
from .serializers import SignatureInviteSerializer
class SignInviteView(APIView):
    def post(self, request, token):
        invite = get_object_or_404(SignatureInvite, token=token)

        if invite.signed:
            return Response({"detail": "Already signed."}, status=status.HTTP_400_BAD_REQUEST)

        signed_pdf = request.FILES.get('signed_pdf')
        if not signed_pdf:
            return Response({"detail": "No signed PDF provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Read content before saving to avoid empty reads
        file_content = signed_pdf.read()
        file_name = signed_pdf.name

        # Save the file to the Document
        document = invite.document
        document.signed_file.save(file_name, ContentFile(file_content))
        document.is_signed = True
        document.save()

        invite.signed = True
        invite.save()

        # Email
        subject = f"Signed Document: {document.title}"
        recipient = invite.email
        context = {
            "document_title": document.title,
            "support_email": dict(settings.ADMINS).get("Support Team", "support@maindodigital.com"),
        }

        html_content = render_to_string("emails/signed_copy_email.html", context)
        text_content = f"Here is your signed copy of '{document.title}'."

        message = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
        )
        message.attach_alternative(html_content, "text/html")
        message.attach(file_name, file_content, "application/pdf")
        message.send()

        return Response({"detail": "Document signed and emailed successfully."}, status=status.HTTP_200_OK)

