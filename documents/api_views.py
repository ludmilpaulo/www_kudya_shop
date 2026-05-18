from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from contas.permissions import IsComplianceAdmin, scope_queryset_for_user
from doctors.models import DoctorProfile
from kudya_platform.audit import record_audit_event
from .models import VerificationDocument
from .serializers import VerificationDocumentSerializer


class VerificationDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = VerificationDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = VerificationDocument.objects.select_related(
            'owner',
            'reviewed_by',
            'country',
            'city',
        )
        if getattr(self.request.user, 'is_platform_admin', False):
            return scope_queryset_for_user(
                self.request.user,
                qs,
                country_lookup='country',
                city_lookup='city',
            )
        return qs.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subject_type = serializer.validated_data['subject_type']
        subject_id = serializer.validated_data['subject_id']

        country = request.user.country
        city = request.user.city
        if subject_type == 'doctor_profile':
            try:
                doctor = DoctorProfile.objects.get(pk=subject_id, user=request.user)
            except DoctorProfile.DoesNotExist:
                return Response(
                    {'subject_id': 'Doctor profile not found for this user.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            country = doctor.country
            city = doctor.city
        elif subject_type == 'user':
            if subject_id != request.user.id:
                return Response(
                    {'subject_id': 'Users may upload only for their own profile.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {'subject_type': 'This subject type is not enabled yet.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = serializer.save(owner=request.user, country=country, city=city)
        record_audit_event(
            request,
            action='verification_document_uploaded',
            target=document,
            country=country,
            city=city,
            metadata={
                'subject_type': document.subject_type,
                'subject_id': document.subject_id,
                'document_type': document.document_type,
            },
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            VerificationDocumentSerializer(document, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=True, methods=['patch'], permission_classes=[IsComplianceAdmin])
    def approve(self, request, pk=None):
        document = self.get_object()
        document.status = 'approved'
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.rejection_reason = ''
        document.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason', 'updated_at'])
        record_audit_event(
            request,
            action='verification_document_approved',
            target=document,
            country=document.country,
            city=document.city,
        )
        return Response(self.get_serializer(document).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsComplianceAdmin])
    def reject(self, request, pk=None):
        document = self.get_object()
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'reason': 'Required.'}, status=status.HTTP_400_BAD_REQUEST)
        document.status = 'rejected'
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.rejection_reason = reason
        document.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason', 'updated_at'])
        record_audit_event(
            request,
            action='verification_document_rejected',
            target=document,
            country=document.country,
            city=document.city,
            metadata={'reason': reason},
        )
        return Response(self.get_serializer(document).data)
