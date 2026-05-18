from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from doctors.models import DoctorProfile, MedicalSpecialty
from kudya_platform.models import AuditEvent, City
from services.models import Country
from .models import VerificationDocument


User = get_user_model()


class VerificationDocumentReviewTests(APITestCase):
    def setUp(self):
        self.temp_media = TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.override.enable()

        self.country = Country.objects.create(name='South Africa', code='ZA', currency='ZAR')
        self.city = City.objects.create(country=self.country, name='Cape Town')
        self.other_country = Country.objects.create(name='Portugal', code='PT', currency='EUR')
        self.other_city = City.objects.create(country=self.other_country, name='Lisbon')
        specialty = MedicalSpecialty.objects.create(slug='cardiologist', name='Cardiologist')
        self.doctor_user = User.objects.create_user(
            username='doctor-cape-town@example.com',
            email='doctor-cape-town@example.com',
            password='StrongPass123!',
            role='doctor',
            country=self.country,
            city=self.city,
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialty=specialty,
            years_experience=12,
            languages='en',
            country=self.country,
            city=self.city,
            consultation_fee='700.00',
            license_number='ZA-999',
        )
        self.in_scope_admin = User.objects.create_user(
            username='compliance-za@example.com',
            email='compliance-za@example.com',
            password='StrongPass123!',
            role='compliance_admin',
            country=self.country,
        )
        self.out_of_scope_admin = User.objects.create_user(
            username='compliance-pt@example.com',
            email='compliance-pt@example.com',
            password='StrongPass123!',
            role='compliance_admin',
            country=self.other_country,
        )

    def tearDown(self):
        self.override.disable()
        self.temp_media.cleanup()
        super().tearDown()

    def _authenticate(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def _upload_document(self):
        self._authenticate(self.doctor_user)
        response = self.client.post(
            '/api/documents/verification-documents/',
            {
                'subject_type': 'doctor_profile',
                'subject_id': self.doctor.id,
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
        return VerificationDocument.objects.get(pk=response.data['id'])

    def test_in_scope_compliance_admin_can_review_document(self):
        document = self._upload_document()
        self._authenticate(self.in_scope_admin)

        response = self.client.patch(f'/api/documents/verification-documents/{document.id}/approve/')

        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.status, 'approved')
        self.assertEqual(document.reviewed_by, self.in_scope_admin)
        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.in_scope_admin,
                action='verification_document_approved',
                country=self.country,
                target_id=str(document.id),
            ).exists()
        )

    def test_out_of_scope_compliance_admin_cannot_review_document(self):
        document = self._upload_document()
        self._authenticate(self.out_of_scope_admin)

        response = self.client.patch(f'/api/documents/verification-documents/{document.id}/approve/')

        self.assertEqual(response.status_code, 404)
        document.refresh_from_db()
        self.assertEqual(document.status, 'pending')
