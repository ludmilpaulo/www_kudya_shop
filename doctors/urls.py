from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedicalSpecialtyViewSet,
    DoctorViewSet,
    AppointmentViewSet,
    doctor_register,
    admin_approve_doctor,
    admin_reject_doctor,
    doctor_verification_documents,
)

router = DefaultRouter()
router.register(r'specialties', MedicalSpecialtyViewSet, basename='medical-specialty')
router.register(r'', DoctorViewSet, basename='doctor')

appointment_router = DefaultRouter()
appointment_router.register(r'', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('register/', doctor_register, name='doctor-register'),
    path('admin/<int:pk>/approve/', admin_approve_doctor, name='admin-approve-doctor'),
    path('admin/<int:pk>/reject/', admin_reject_doctor, name='admin-reject-doctor'),
    path('<int:pk>/documents/', doctor_verification_documents, name='doctor-verification-documents'),
    path('', include(router.urls)),
]

appointment_urlpatterns = [
    path('book/', AppointmentViewSet.as_view({'post': 'create'}), name='appointment-book'),
    path('history/', AppointmentViewSet.as_view({'get': 'history'}), name='appointment-history'),
    path('<int:pk>/cancel/', AppointmentViewSet.as_view({'patch': 'cancel'}), name='appointment-cancel'),
    path('<int:pk>/reschedule/', AppointmentViewSet.as_view({'patch': 'reschedule'}), name='appointment-reschedule'),
    path('<int:pk>/confirm/', AppointmentViewSet.as_view({'patch': 'confirm'}), name='appointment-confirm'),
]
