from datetime import time, timedelta
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from documents.models import VerificationDocument
from kudya_platform.models import AuditEvent, City, CountryComplianceSetting
from services.models import Country
from .models import MedicalSpecialty, DoctorProfile, DoctorAvailability


User = get_user_model()


class DoctorBookingFoundationTests(APITestCase):
    def setUp(self):
        self.country = Country.objects.create(name='South Africa', code='ZA', currency='ZAR')
        self.city = City.objects.create(country=self.country, name='Johannesburg')
        self.specialty = MedicalSpecialty.objects.create(slug='gp', name='General Practitioner')
        self.doctor_user = User.objects.create_user(
            username='doctor@example.com',
            email='doctor@example.com',
            password='StrongPass123!',
            role='doctor',
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialty=self.specialty,
            years_experience=10,
            languages='en',
            country=self.country,
            city=self.city,
            consultation_fee='500.00',
            online_consultation_enabled=True,
            physical_consultation_enabled=True,
            license_number='ZA-123',
            approval_status='approved',
        )
        self.customer = User.objects.create_user(
            username='customer@example.com',
            email='customer@example.com',
            password='StrongPass123!',
            role='customer',
        )
        self.booking_date = timezone.localdate() + timedelta(days=7)
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=self.booking_date.weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            consultation_type='both',
        )
        CountryComplianceSetting.objects.create(
            country=self.country,
            online_consultations_allowed=False,
        )
        access = RefreshToken.for_user(self.customer).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    def test_online_booking_respects_country_compliance(self):
        response = self.client.post(
            '/api/appointments/book/',
            {
                'doctor': self.doctor.id,
                'appointment_type': 'online',
                'date': self.booking_date.isoformat(),
                'start_time': '09:00',
                'end_time': '09:30',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('appointment_type', response.data)

    def test_booking_rejects_overlapping_slots(self):
        payload = {
            'doctor': self.doctor.id,
            'appointment_type': 'physical',
            'date': self.booking_date.isoformat(),
            'start_time': '09:00',
            'end_time': '09:30',
        }
        first = self.client.post('/api/appointments/book/', payload, format='json')
        second = self.client.post('/api/appointments/book/', payload, format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertIn('start_time', second.data)


class DoctorApprovalPermissionTests(APITestCase):
    def setUp(self):
        self.country = Country.objects.create(name='Mozambique', code='MZ', currency='MZN')
        self.other_country = Country.objects.create(name='Angola', code='AO', currency='AOA')
        specialty = MedicalSpecialty.objects.create(slug='dentist', name='Dentist')
        doctor_user = User.objects.create_user(
            username='pending-doctor@example.com',
            email='pending-doctor@example.com',
            password='StrongPass123!',
            role='doctor',
        )
        self.doctor = DoctorProfile.objects.create(
            user=doctor_user,
            specialty=specialty,
            years_experience=4,
            languages='pt',
            country=self.country,
            consultation_fee='300.00',
            online_consultation_enabled=False,
            physical_consultation_enabled=True,
            license_number='MZ-456',
        )
        CountryComplianceSetting.objects.create(
            country=self.country,
            required_doctor_documents=['license', 'identity'],
        )

    def _authenticate_admin(self, *, country):
        admin = User.objects.create_user(
            username=f'compliance-{country.code.lower()}@example.com',
            email=f'compliance-{country.code.lower()}@example.com',
            password='StrongPass123!',
            role='compliance_admin',
            country=country,
        )
        token = RefreshToken.for_user(admin).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return admin

    def _approve_required_document(self, document_type):
        return VerificationDocument.objects.create(
            owner=self.doctor.user,
            subject_type='doctor_profile',
            subject_id=self.doctor.id,
            document_type=document_type,
            file=f'verification_documents/{document_type}.pdf',
            country=self.country,
            status='approved',
        )

    def test_compliance_admin_can_approve_doctor_with_scope_and_required_documents(self):
        admin = self._authenticate_admin(country=self.country)
        self._approve_required_document('license')
        self._approve_required_document('identity')

        response = self.client.patch(f'/api/doctors/admin/{self.doctor.id}/approve/')

        self.assertEqual(response.status_code, 200)
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.approval_status, 'approved')
        self.assertTrue(
            AuditEvent.objects.filter(
                actor=admin,
                action='doctor_approved',
                country=self.country,
            ).exists()
        )

    def test_approval_requires_country_configured_documents(self):
        self._authenticate_admin(country=self.country)

        response = self.client.patch(f'/api/doctors/admin/{self.doctor.id}/approve/')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['missing_documents'], ['identity', 'license'])

    def test_compliance_admin_cannot_approve_doctor_outside_scope(self):
        self._authenticate_admin(country=self.other_country)
        self._approve_required_document('license')
        self._approve_required_document('identity')

        response = self.client.patch(f'/api/doctors/admin/{self.doctor.id}/approve/')

        self.assertEqual(response.status_code, 403)
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.approval_status, 'pending')


class DoctorVerificationDocumentTests(APITestCase):
    def setUp(self):
        self.temp_media = TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.override.enable()
        self.country = Country.objects.create(name='France', code='FR', currency='EUR')
        self.city = City.objects.create(country=self.country, name='Paris')
        specialty = MedicalSpecialty.objects.create(slug='dermatologist', name='Dermatologist')
        self.doctor_user = User.objects.create_user(
            username='doctor-paris@example.com',
            email='doctor-paris@example.com',
            password='StrongPass123!',
            role='doctor',
            country=self.country,
            city=self.city,
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialty=specialty,
            years_experience=8,
            languages='fr,en',
            country=self.country,
            city=self.city,
            consultation_fee='120.00',
            license_number='FR-789',
        )
        token = RefreshToken.for_user(self.doctor_user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def tearDown(self):
        self.override.disable()
        self.temp_media.cleanup()
        super().tearDown()

    def test_doctor_can_upload_verification_document_with_scoped_audit_event(self):
        response = self.client.post(
            f'/api/doctors/{self.doctor.id}/documents/',
            {
                'document_type': 'license',
                'file': SimpleUploadedFile(
                    'license.pdf',
                    b'%PDF-1.4 doctor license',
                    content_type='application/pdf',
                ),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        document = VerificationDocument.objects.get(pk=response.data['id'])
        self.assertEqual(document.owner, self.doctor_user)
        self.assertEqual(document.country, self.country)
        self.assertEqual(document.city, self.city)
        self.assertEqual(document.status, 'pending')
        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.doctor_user,
                action='doctor_document_uploaded',
                country=self.country,
                city=self.city,
                target_id=str(document.id),
            ).exists()
        )
