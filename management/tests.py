from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accommodation.models import AccommodationBooking, AccommodationListing
from customers.models import Customer
from deliveries.models import PackageDelivery
from drivers.models import Driver
from kudya_platform.models import City
from properties.models import PropertyEnquiry
from services.models import Booking, Service, ServiceCategory
from stores.models import Store, StoreCategory, StoreType
from support.models import SupportTicket
from rides.models import Ride
from services.models import Country


User = get_user_model()


class ScopedAdminDashboardTests(APITestCase):
    def setUp(self):
        self.country = Country.objects.create(name='South Africa', code='ZA', currency='ZAR')
        self.city = City.objects.create(country=self.country, name='Johannesburg')
        self.other_country = Country.objects.create(name='Mozambique', code='MZ', currency='MZN')
        self.other_city = City.objects.create(country=self.other_country, name='Maputo')
        self.admin = User.objects.create_user(
            username='country-admin-za@example.com',
            email='country-admin-za@example.com',
            password='StrongPass123!',
            role='country_admin',
            country=self.country,
        )
        self.customer = User.objects.create_user(
            username='customer-za@example.com',
            email='customer-za@example.com',
            password='StrongPass123!',
            role='customer',
            country=self.country,
            city=self.city,
        )
        self.other_customer = User.objects.create_user(
            username='customer-mz@example.com',
            email='customer-mz@example.com',
            password='StrongPass123!',
            role='customer',
            country=self.other_country,
            city=self.other_city,
        )
        self.ride = Ride.objects.create(
            customer=self.customer,
            country=self.country,
            city=self.city,
            pickup_address='A',
            pickup_lat='-26.2041000',
            pickup_lng='28.0473000',
            destination_address='B',
            destination_lat='-26.1000000',
            destination_lng='28.1000000',
            status='accepted',
        )
        self.other_ride = Ride.objects.create(
            customer=self.other_customer,
            country=self.other_country,
            city=self.other_city,
            pickup_address='C',
            pickup_lat='-25.9655000',
            pickup_lng='32.5832000',
            destination_address='D',
            destination_lat='-25.9500000',
            destination_lng='32.6000000',
            status='accepted',
        )
        token = RefreshToken.for_user(self.admin).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_dashboard_metrics_are_limited_to_admin_country_scope(self):
        response = self.client.get('/api/admin/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rides_today'], 1)
        self.assertEqual(response.data['rides_active'], 1)
        self.assertEqual(response.data['total_users'], 2)

    def test_platform_admin_ride_list_is_limited_to_scope(self):
        response = self.client.get('/api/rides/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.ride.id)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DayToDayOperationsTests(APITestCase):
    def setUp(self):
        self.country = Country.objects.create(name='South Africa', code='ZA', currency='ZAR')
        self.city = City.objects.create(country=self.country, name='Johannesburg')
        self.customer_user = User.objects.create_user(
            username='customer-ops@example.com',
            email='customer-ops@example.com',
            password='StrongPass123!',
            role='customer',
            country=self.country,
            city=self.city,
        )
        self.customer = Customer.objects.create(user=self.customer_user)
        self.driver_user = User.objects.create_user(
            username='driver-ops@example.com',
            email='driver-ops@example.com',
            password='StrongPass123!',
            role='driver',
            country=self.country,
            city=self.city,
        )
        self.driver = Driver.objects.create(
            user=self.driver_user,
            is_online=True,
            is_available=True,
            is_verified=True,
        )
        self.provider_user = User.objects.create_user(
            username='provider-ops@example.com',
            email='provider-ops@example.com',
            password='StrongPass123!',
            role='service_provider',
            country=self.country,
            city=self.city,
        )
        store_type = StoreType.objects.create(name='Professional Services')
        store_category = StoreCategory.objects.create(name='Home Services', slug='home-services')
        self.provider_store = Store.objects.create(
            user=self.provider_user,
            store_type=store_type,
            category=store_category,
            name='Kudya Home Services',
            phone='0123456789',
            address='1 Market Street',
        )
        service_category = ServiceCategory.objects.create(
            name='Plumbers',
            slug='plumbers',
            category_type='home',
        )
        self.service = Service.objects.create(
            parceiro=self.provider_store,
            category=service_category,
            title='Emergency plumbing',
            description='Fix leaks',
            price='450.00',
            currency='ZAR',
            duration_minutes=60,
            instant_booking=False,
        )
        self.host_user = User.objects.create_user(
            username='host-ops@example.com',
            email='host-ops@example.com',
            password='StrongPass123!',
            role='host',
            country=self.country,
            city=self.city,
        )
        self.listing = AccommodationListing.objects.create(
            host=self.host_user,
            title='City apartment',
            property_type='apartment',
            description='Central stay',
            country=self.country,
            city=self.city,
            address='2 Main Road',
            price_per_night='900.00',
            currency='ZAR',
            approval_status='approved',
        )
        self.support_user = User.objects.create_user(
            username='support-ops@example.com',
            email='support-ops@example.com',
            password='StrongPass123!',
            role='support',
            country=self.country,
        )
        self.agent_user = User.objects.create_user(
            username='agent-ops@example.com',
            email='agent-ops@example.com',
            password='StrongPass123!',
            role='agent',
            country=self.country,
            city=self.city,
        )

    def _authenticate(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_customer_driver_and_courier_can_complete_daily_mobility_flows(self):
        self._authenticate(self.customer_user)
        top_up = self.client.post('/api/wallet/top_up/', {'amount': '250.00', 'currency': 'ZAR'}, format='json')
        ride = self.client.post(
            '/api/rides/',
            {
                'pickup_address': 'A',
                'pickup_lat': '-26.2041000',
                'pickup_lng': '28.0473000',
                'destination_address': 'B',
                'destination_lat': '-26.1000000',
                'destination_lng': '28.1000000',
                'country': self.country.id,
                'city': self.city.id,
            },
            format='json',
        )
        package = self.client.post(
            '/api/deliveries/',
            {
                'package_type': 'small',
                'urgency': 'standard',
                'pickup_address': 'A',
                'pickup_lat': '-26.2041000',
                'pickup_lng': '28.0473000',
                'dropoff_address': 'B',
                'dropoff_lat': '-26.1000000',
                'dropoff_lng': '28.1000000',
                'recipient_name': 'Ada',
                'recipient_phone': '0123456789',
            },
            format='json',
        )
        self.assertEqual(top_up.status_code, 201)
        self.assertEqual(ride.status_code, 201)
        self.assertEqual(package.status_code, 201)

        self._authenticate(self.driver_user)
        accepted_ride = self.client.post(f"/api/rides/{ride.data['id']}/accept/")
        arrived = self.client.post(f"/api/rides/{ride.data['id']}/arrived/")
        started = self.client.post(f"/api/rides/{ride.data['id']}/start/")
        completed = self.client.post(f"/api/rides/{ride.data['id']}/complete/", {'final_price': '120.00'}, format='json')
        available_packages = self.client.get('/api/deliveries/')
        accepted_package = self.client.post(f"/api/deliveries/{package.data['id']}/accept/")
        delivered_package = self.client.patch(
            f"/api/deliveries/{package.data['id']}/status/",
            {'status': 'delivered'},
            format='json',
        )

        self.assertEqual(accepted_ride.status_code, 200)
        self.assertEqual(arrived.status_code, 200)
        self.assertEqual(started.status_code, 200)
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.data['status'], 'completed')
        self.assertEqual(len(available_packages.data), 1)
        self.assertEqual(accepted_package.status_code, 200)
        self.assertEqual(delivered_package.status_code, 200)
        self.assertEqual(delivered_package.data['status'], 'delivered')

    def test_service_provider_can_confirm_start_and_complete_customer_booking(self):
        self._authenticate(self.customer_user)
        booking = self.client.post(
            '/api/services/bookings/',
            {
                'service': self.service.id,
                'customer': self.customer.id,
                'booking_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'booking_time': '09:00',
                'duration_minutes': 60,
                'payment_method': 'wallet',
            },
            format='json',
        )
        self.assertEqual(booking.status_code, 201)
        self.assertEqual(booking.data['status'], 'pending')

        self._authenticate(self.provider_user)
        confirmed = self.client.post(f"/api/services/bookings/{booking.data['id']}/confirm/")
        started = self.client.post(f"/api/services/bookings/{booking.data['id']}/start/")
        completed = self.client.post(f"/api/services/bookings/{booking.data['id']}/complete/")

        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(started.status_code, 200)
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(Booking.objects.get(pk=booking.data['id']).status, 'completed')

    def test_customer_and_host_can_manage_accommodation_booking_history(self):
        self._authenticate(self.customer_user)
        booking = self.client.post(
            '/api/accommodation/bookings/',
            {
                'listing': self.listing.id,
                'check_in': (timezone.localdate() + timedelta(days=7)).isoformat(),
                'check_out': (timezone.localdate() + timedelta(days=9)).isoformat(),
                'guests': 2,
            },
            format='json',
        )
        customer_history = self.client.get('/api/accommodation/bookings/history/')

        self.assertEqual(booking.status_code, 201)
        self.assertEqual(len(customer_history.data), 1)
        self.assertEqual(customer_history.data[0]['id'], booking.data['id'])

        self._authenticate(self.host_user)
        host_history = self.client.get('/api/accommodation/bookings/history/')

        self.assertEqual(len(host_history.data), 1)
        self.assertEqual(host_history.data[0]['id'], booking.data['id'])

    def test_customer_and_support_agent_can_complete_ticket_lifecycle(self):
        self._authenticate(self.customer_user)
        ticket = self.client.post(
            '/api/support/tickets/',
            {
                'category': 'payment',
                'subject': 'Refund needed',
                'message': 'Duplicate charge',
            },
            format='json',
        )
        self.assertEqual(ticket.status_code, 201)

        self._authenticate(self.support_user)
        updated = self.client.patch(
            f"/api/support/tickets/{ticket.data['id']}/",
            {'status': 'resolved', 'priority': 'high'},
            format='json',
        )

        self.assertEqual(updated.status_code, 200)
        support_ticket = SupportTicket.objects.get(pk=ticket.data['id'])
        self.assertEqual(support_ticket.status, 'resolved')
        self.assertEqual(support_ticket.priority, 'high')

    def test_property_agent_and_customer_can_complete_enquiry_lifecycle(self):
        self._authenticate(self.agent_user)
        created = self.client.post(
            '/api/properties/create/',
            {
                'title': 'Family home',
                'description': 'Three-bedroom rental',
                'address': '3 Oak Street',
                'city': 'Johannesburg',
                'suburb': 'Rosebank',
                'country': self.country.id,
                'listing_type': 'rent_monthly',
                'property_type': 'house',
                'price': '18000.00',
                'monthly_rent': '18000.00',
                'deposit': '18000.00',
                'bedrooms': 3,
                'bathrooms': 2,
            },
            format='json',
        )
        self.assertEqual(created.status_code, 201)
        property_id = created.data['id']
        from properties.models import Property
        Property.objects.filter(pk=property_id).update(is_approved=True, approval_status='approved')

        self._authenticate(self.customer_user)
        search = self.client.get('/api/properties/search/?listing_type=rent_monthly&city=Johannesburg')
        enquiry = self.client.post(
            f'/api/properties/{property_id}/enquiry/',
            {
                'enquiry_type': 'viewing',
                'message': 'Can I view this on Saturday?',
            },
            format='json',
        )
        self.assertEqual(search.status_code, 200)
        self.assertEqual(len(search.data), 1)
        self.assertEqual(enquiry.status_code, 201)

        self._authenticate(self.agent_user)
        updated = self.client.patch(
            f"/api/properties/enquiries/{enquiry.data['id']}/status/",
            {'status': 'scheduled'},
            format='json',
        )

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(PropertyEnquiry.objects.get(pk=enquiry.data['id']).status, 'scheduled')
