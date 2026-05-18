from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from services.models import Country
from .models import AuditEvent, City, Translation, CountryComplianceSetting


User = get_user_model()


class PlatformTranslationTests(APITestCase):
    def test_translation_bundle_merges_english_fallback_with_requested_language(self):
        Translation.objects.create(
            key='common.greeting',
            language='en',
            value='Hello',
            module='common',
        )
        Translation.objects.create(
            key='common.greeting',
            language='fr',
            value='Bonjour',
            module='common',
        )
        Translation.objects.create(
            key='common.checkout',
            language='en',
            value='Checkout',
            module='common',
        )

        response = self.client.get('/api/translations/?lang=fr')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['common.greeting'], 'Bonjour')
        self.assertEqual(response.data['common.checkout'], 'Checkout')


class CountryComplianceTests(APITestCase):
    def test_compliance_endpoint_exposes_country_rules(self):
        country = Country.objects.create(name='South Africa', code='ZA', currency='ZAR')
        CountryComplianceSetting.objects.create(
            country=country,
            online_consultations_allowed=True,
            prescriptions_allowed=False,
            required_doctor_documents=['license', 'identity'],
        )

        response = self.client.get('/api/platform/compliance/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertTrue(response.data[0]['online_consultations_allowed'])
        self.assertEqual(response.data[0]['required_doctor_documents'], ['license', 'identity'])


class AuditEventScopeTests(APITestCase):
    def setUp(self):
        self.country = Country.objects.create(name='South Africa', code='ZA', currency='ZAR')
        self.city_one = City.objects.create(country=self.country, name='Johannesburg')
        self.city_two = City.objects.create(country=self.country, name='Cape Town')
        self.other_country = Country.objects.create(name='Angola', code='AO', currency='AOA')
        self.other_city = City.objects.create(country=self.other_country, name='Luanda')
        self.country_admin = User.objects.create_user(
            username='country-admin@example.com',
            email='country-admin@example.com',
            password='StrongPass123!',
            role='country_admin',
            country=self.country,
        )
        self.city_admin = User.objects.create_user(
            username='city-admin@example.com',
            email='city-admin@example.com',
            password='StrongPass123!',
            role='city_admin',
            country=self.country,
            city=self.city_one,
        )
        for city in (self.city_one, self.city_two, self.other_city):
            AuditEvent.objects.create(
                actor=self.country_admin,
                action='scope_test',
                target_type='City',
                target_id=str(city.id),
                target_repr=str(city),
                country=city.country,
                city=city,
            )

    def _authenticate(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_country_admin_sees_only_events_in_their_country(self):
        self._authenticate(self.country_admin)

        response = self.client.get('/api/platform/audit-events/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({item['country'] for item in response.data}, {self.country.id})

    def test_city_admin_sees_only_events_in_their_city(self):
        self._authenticate(self.city_admin)

        response = self.client.get('/api/platform/audit-events/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['city'], self.city_one.id)
