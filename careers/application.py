from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework.pagination import PageNumberPagination
import mimetypes
from .models import JobApplication
from .serializers import JobApplicationSerializer


class JobApplicationPagination(PageNumberPagination):
    page_size = 5


class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all().order_by('-submitted_at')
    serializer_class = JobApplicationSerializer
    pagination_class = JobApplicationPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        print("📥 [CREATE] Incoming data:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("🚨 [CREATE] Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        application = serializer.instance
        print("✅ [CREATE] Application created for:", application.full_name)

        self.send_hr_email(application)
        self.send_applicant_email(application)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        print("🔁 [UPDATE] PATCH request received:", request.data)

        instance = self.get_object()
        previous_status = instance.status
        print("🟡 [UPDATE] Previous status:", previous_status)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_status = serializer.validated_data.get('status')
        print("🟢 [UPDATE] Incoming status:", updated_status)

        self.perform_update(serializer)
        print("✅ [UPDATE] New saved status:", self.get_object().status)

        if updated_status and updated_status != previous_status:
            print("📨 [UPDATE] Status changed — triggering email...")
            self.send_status_update_email(self.get_object())
        else:
            print("🚫 [UPDATE] No status change — skipping email")

        return Response(serializer.data)

    def send_hr_email(self, application):
        try:
            print("📧 [HR EMAIL] Sending HR email for:", application.full_name)
            hr_html = render_to_string("emails/hr_notification.html", {
                "full_name": application.full_name,
                "email": application.email,
                "title": application.career.title,
                "location": application.career.location,
                "cover_letter": application.cover_letter,
            })

            email = EmailMessage(
                subject=f"New Application – {application.career.title}",
                body=hr_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.HR_NOTIFICATION_EMAIL],
            )
            email.content_subtype = "html"

            if application.resume:
                resume_file = application.resume
                mime_type, _ = mimetypes.guess_type(resume_file.name)
                email.attach(
                    resume_file.name,
                    resume_file.read(),
                    mime_type or 'application/octet-stream'
                )

            email.send(fail_silently=False)
            print("✅ [HR EMAIL] Email sent")
        except Exception as e:
            print("❌ [HR EMAIL] Failed:", str(e))

    def send_applicant_email(self, application):
        try:
            print("📧 [APPLICANT EMAIL] Sending confirmation email to:", application.email)
            lang = getattr(application, 'language', 'en') or 'en'
            context = {
                "full_name": application.full_name,
                "title": application.career.title,
            }
            template = "emails/pt/applicant_confirmation.html" if lang == 'pt' else "emails/en/applicant_confirmation.html"
            html = render_to_string(template, context)

            confirmation = EmailMessage(
                subject=f"Application Received – {application.career.title}",
                body=html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[application.email],
            )
            confirmation.content_subtype = "html"
            confirmation.send(fail_silently=False)
            print("✅ [APPLICANT EMAIL] Email sent")
        except Exception as e:
            print("❌ [APPLICANT EMAIL] Failed:", str(e))

    def send_status_update_email(self, application):
        try:
            print("📧 [STATUS EMAIL] Preparing status update email for:", application.email)
            lang = getattr(application, 'language', 'en') or 'en'
            context = {
                "full_name": application.full_name,
                "title": application.career.title,
                "status": application.status,
            }

            email_data = self.get_subject_and_intro(lang, application.status, application.career.title)
            print("✉️ [STATUS EMAIL] Subject:", email_data.get("subject"))
            print("📝 [STATUS EMAIL] Intro:", email_data.get("intro"))

            context["intro"] = email_data.get("intro", "")

            template = f"emails/{lang}/status_update.html"
            html = render_to_string(template, context)

            email = EmailMessage(
                subject=email_data.get("subject", f"Application Update – {application.career.title}"),
                body=html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[application.email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)
            print("✅ [STATUS EMAIL] Sent successfully")
        except Exception as e:
            print("❌ [STATUS EMAIL] Failed:", str(e))

    def get_subject_and_intro(self, lang, status, title):
        status_map = {
            "en": {
                "submitted": {
                    "subject": f"Application Received – {title}",
                    "intro": "Thank you for submitting your application. It has been received and is under review.",
                },
                "processing": {
                    "subject": f"Application Under Review – {title}",
                    "intro": "Your application is currently being processed by our team.",
                },
                "review": {
                    "subject": f"Application in Review – {title}",
                    "intro": "Your application is now in the review stage with our hiring team.",
                },
                "approved": {
                    "subject": f"Congratulations! You're Approved – {title}",
                    "intro": "We're excited to inform you that your application has been approved.",
                },
                "rejected": {
                    "subject": f"Update on Your Application – {title}",
                    "intro": "We appreciate your interest. Unfortunately, your application was not selected.",
                },
            },
            "pt": {
                "submitted": {
                    "subject": f"Candidatura Recebida – {title}",
                    "intro": "Obrigado por enviar sua candidatura. Ela foi recebida e está em análise.",
                },
                "processing": {
                    "subject": f"Candidatura em Processamento – {title}",
                    "intro": "Sua candidatura está sendo processada pela nossa equipe.",
                },
                "review": {
                    "subject": f"Candidatura em Avaliação – {title}",
                    "intro": "Sua candidatura está agora em fase de avaliação com a equipe de recrutamento.",
                },
                "approved": {
                    "subject": f"Parabéns! Aprovado – {title}",
                    "intro": "Temos o prazer de informar que sua candidatura foi aprovada.",
                },
                "rejected": {
                    "subject": f"Atualização da Candidatura – {title}",
                    "intro": "Agradecemos seu interesse. Infelizmente, sua candidatura não foi selecionada.",
                },
            },
        }
        return status_map.get(lang, status_map["en"]).get(status, {})
