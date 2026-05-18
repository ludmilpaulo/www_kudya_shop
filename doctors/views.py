from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import MedicalSpecialty, DoctorProfile, DoctorAvailability, Appointment, DoctorDocument
from .serializers import (
    MedicalSpecialtySerializer,
    DoctorListSerializer,
    DoctorDetailSerializer,
    DoctorRegisterSerializer,
    DoctorAvailabilitySerializer,
    AppointmentSerializer,
    AppointmentBookSerializer,
)
from contas.permissions import IsComplianceAdmin
from contas.permissions import user_can_access_scope, scope_queryset_for_user
from documents.models import VerificationDocument
from documents.serializers import VerificationDocumentSerializer
from kudya_platform.audit import record_audit_event
from kudya_platform.models import CountryComplianceSetting


class MedicalSpecialtyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MedicalSpecialty.objects.filter(is_active=True)
    serializer_class = MedicalSpecialtySerializer
    permission_classes = [AllowAny]


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """Public doctor search — only approved doctors."""
    serializer_class = DoctorListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialty', 'country', 'city', 'online_consultation_enabled', 'physical_consultation_enabled']
    search_fields = ['user__first_name', 'user__last_name', 'clinic_name', 'biography']
    ordering_fields = ['consultation_fee', 'rating', 'years_experience']
    ordering = ['-rating']

    def get_queryset(self):
        qs = DoctorProfile.objects.filter(
            approval_status='approved',
            is_active=True,
        ).select_related('user', 'specialty', 'country', 'city')

        specialty_slug = self.request.query_params.get('specialty_slug')
        if specialty_slug:
            qs = qs.filter(specialty__slug=specialty_slug)

        language = self.request.query_params.get('language')
        if language:
            qs = qs.filter(languages__icontains=language)

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            qs = qs.filter(consultation_fee__gte=min_price)
        if max_price:
            qs = qs.filter(consultation_fee__lte=max_price)

        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            qs = qs.filter(rating__gte=min_rating)

        consultation_type = self.request.query_params.get('consultation_type')
        if consultation_type == 'online':
            qs = qs.filter(online_consultation_enabled=True)
        elif consultation_type == 'physical':
            qs = qs.filter(physical_consultation_enabled=True)

        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DoctorDetailSerializer
        return DoctorListSerializer

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        doctor = self.get_object()
        slots = DoctorAvailability.objects.filter(doctor=doctor, is_available=True)
        return Response(DoctorAvailabilitySerializer(slots, many=True).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def doctor_register(request):
    serializer = DoctorRegisterSerializer(data=request.data)
    if serializer.is_valid():
        doctor = serializer.save()
        return Response(
            DoctorDetailSerializer(doctor).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentBookSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_platform_admin', False):
            qs = Appointment.objects.all().select_related('doctor__user', 'customer')
            return scope_queryset_for_user(
                user,
                qs,
                country_lookup='doctor__country',
                city_lookup='doctor__city',
            )
        if hasattr(user, 'doctor_profile'):
            return Appointment.objects.filter(doctor=user.doctor_profile)
        return Appointment.objects.filter(customer=user)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        qs = self.get_queryset().order_by('-date', '-start_time')
        return Response(AppointmentSerializer(qs, many=True).data)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'cancelled'
        appointment.cancellation_reason = request.data.get('reason', '')
        appointment.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=['patch'])
    def reschedule(self, request, pk=None):
        appointment = self.get_object()
        for field in ('date', 'start_time', 'end_time'):
            if field in request.data:
                setattr(appointment, field, request.data[field])
        appointment.status = 'pending'
        appointment.save()
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        if not hasattr(request.user, 'doctor_profile') or appointment.doctor != request.user.doctor_profile:
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
        appointment.status = 'confirmed'
        appointment.save(update_fields=['status', 'updated_at'])
        return Response(AppointmentSerializer(appointment).data)


@api_view(['PATCH'])
@permission_classes([IsComplianceAdmin])
def admin_approve_doctor(request, pk):
    try:
        doctor = DoctorProfile.objects.get(pk=pk)
    except DoctorProfile.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    if not user_can_access_scope(request.user, doctor.country_id, doctor.city_id):
        return Response({'detail': 'Outside your admin scope.'}, status=status.HTTP_403_FORBIDDEN)
    compliance = CountryComplianceSetting.objects.filter(
        country=doctor.country,
        is_active=True,
    ).first()
    required_documents = compliance.required_doctor_documents if compliance else []
    approved_shared_documents = set(
        VerificationDocument.objects.filter(
            subject_type='doctor_profile',
            subject_id=doctor.id,
            status='approved',
        ).values_list('document_type', flat=True)
    )
    approved_legacy_documents = set(
        DoctorDocument.objects.filter(doctor=doctor, verified=True).values_list('doc_type', flat=True)
    )
    missing_documents = sorted(
        set(required_documents) - approved_shared_documents - approved_legacy_documents
    )
    if missing_documents:
        return Response(
            {
                'detail': 'Required doctor documents are not approved.',
                'missing_documents': missing_documents,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    doctor.approval_status = 'approved'
    doctor.save(update_fields=['approval_status', 'updated_at'])
    record_audit_event(
        request,
        action='doctor_approved',
        target=doctor,
        country=doctor.country,
        city=doctor.city,
    )
    return Response(DoctorDetailSerializer(doctor).data)


@api_view(['PATCH'])
@permission_classes([IsComplianceAdmin])
def admin_reject_doctor(request, pk):
    try:
        doctor = DoctorProfile.objects.get(pk=pk)
    except DoctorProfile.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    if not user_can_access_scope(request.user, doctor.country_id, doctor.city_id):
        return Response({'detail': 'Outside your admin scope.'}, status=status.HTTP_403_FORBIDDEN)
    doctor.approval_status = 'rejected'
    doctor.rejection_reason = request.data.get('reason', '')
    doctor.save(update_fields=['approval_status', 'rejection_reason', 'updated_at'])
    record_audit_event(
        request,
        action='doctor_rejected',
        target=doctor,
        country=doctor.country,
        city=doctor.city,
        metadata={'reason': doctor.rejection_reason},
    )
    return Response(DoctorDetailSerializer(doctor).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def doctor_verification_documents(request, pk):
    try:
        doctor = DoctorProfile.objects.get(pk=pk)
    except DoctorProfile.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    is_owner = doctor.user_id == request.user.id
    is_scoped_admin = getattr(request.user, 'is_platform_admin', False) and user_can_access_scope(
        request.user,
        doctor.country_id,
        doctor.city_id,
    )
    if not is_owner and not is_scoped_admin:
        return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        documents = VerificationDocument.objects.filter(
            subject_type='doctor_profile',
            subject_id=doctor.id,
        ).select_related('owner', 'reviewed_by', 'country', 'city')
        return Response(
            VerificationDocumentSerializer(documents, many=True, context={'request': request}).data
        )

    if not is_owner:
        return Response({'detail': 'Only the doctor can upload documents.'}, status=status.HTTP_403_FORBIDDEN)

    document_type = request.data.get('document_type')
    file_obj = request.FILES.get('file')
    if not document_type or not file_obj:
        return Response(
            {'detail': 'document_type and file are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = VerificationDocumentSerializer(
        data={
            'subject_type': 'doctor_profile',
            'subject_id': doctor.id,
            'document_type': document_type,
            'file': file_obj,
        },
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    document = serializer.save(
        owner=request.user,
        country=doctor.country,
        city=doctor.city,
    )
    record_audit_event(
        request,
        action='doctor_document_uploaded',
        target=document,
        country=doctor.country,
        city=doctor.city,
        metadata={'document_type': document.document_type, 'doctor_id': doctor.id},
    )
    return Response(
        VerificationDocumentSerializer(document, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )
