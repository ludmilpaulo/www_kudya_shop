"""Seed Kudya super-app platform data: modules, specialties, translations, countries."""
from django.core.management.base import BaseCommand
from services.models import Country, Province
from kudya_platform.models import PlatformModule, Translation, City
from doctors.models import MedicalSpecialty


MODULES = [
    ('food', 'Food', 'utensils', '#F59E0B', '#D97706', 1),
    ('groceries', 'Grocery', 'shopping-basket', '#10B981', '#059669', 2),
    ('rides', 'Rides', 'car', '#3B82F6', '#1D4ED8', 3),
    ('package', 'SendPackage', 'package', '#8B5CF6', '#6D28D9', 4),
    ('car_rental', 'CarRental', 'car-side', '#06B6D4', '#0891B2', 5),
    ('doctors', 'Doctors', 'stethoscope', '#EF4444', '#B91C1C', 6),
    ('services', 'Services', 'briefcase', '#6366F1', '#4338CA', 7),
    ('accommodation', 'Accommodation', 'bed', '#EC4899', '#BE185D', 8),
    ('property', 'Properties', 'home', '#14B8A6', '#0F766E', 9),
    ('wallet', 'Wallet', 'wallet', '#F97316', '#C2410C', 10),
    ('business', 'ComingSoon', 'building', '#64748B', '#334155', 11),
]

SPECIALTIES = [
    ('general', 'General Practitioner', 1),
    ('dentist', 'Dentist', 2),
    ('dermatologist', 'Dermatologist', 3),
    ('gynecologist', 'Gynecologist', 4),
    ('pediatrician', 'Pediatrician', 5),
    ('psychologist', 'Psychologist', 6),
    ('physiotherapist', 'Physiotherapist', 7),
    ('cardiologist', 'Cardiologist', 8),
    ('orthopedic', 'Orthopedic Doctor', 9),
    ('optometrist', 'Eye Doctor / Optometrist', 10),
    ('ent', 'ENT Specialist', 11),
    ('nutritionist', 'Nutritionist', 12),
    ('mental_health', 'Mental Health Professional', 13),
    ('other', 'Other Specialist', 99),
]

COUNTRIES = [
    ('South Africa', 'ZA', 'ZAR', 'Africa/Johannesburg'),
    ('Mozambique', 'MZ', 'MZN', 'Africa/Maputo'),
    ('Angola', 'AO', 'AOA', 'Africa/Luanda'),
    ('Portugal', 'PT', 'EUR', 'Europe/Lisbon'),
]

HOME_TRANSLATIONS = {
    'en': {
        'app.tagline': 'Your life, one app',
        'home.greeting': 'What do you need today?',
        'module.food.title': 'Food',
        'module.food.subtitle': 'Restaurants & meals',
        'module.groceries.title': 'Groceries',
        'module.groceries.subtitle': 'Shops near you',
        'module.rides.title': 'Rides',
        'module.rides.subtitle': 'Get there fast',
        'module.package.title': 'Send Package',
        'module.package.subtitle': 'Courier delivery',
        'module.car_rental.title': 'Car Rental',
        'module.car_rental.subtitle': 'Rent a vehicle',
        'module.doctors.title': 'Doctors',
        'module.doctors.subtitle': 'Book consultations',
        'module.services.title': 'Services',
        'module.services.subtitle': 'Local professionals',
        'module.accommodation.title': 'Stay',
        'module.accommodation.subtitle': 'Book accommodation',
        'module.property.title': 'Property',
        'module.property.subtitle': 'Rent or buy',
        'module.wallet.title': 'Wallet',
        'module.wallet.subtitle': 'Pay & manage money',
        'module.business.title': 'Business',
        'module.business.subtitle': 'Corporate accounts',
    },
    'pt': {
        'app.tagline': 'A sua vida, numa app',
        'home.greeting': 'O que precisa hoje?',
        'module.food.title': 'Comida',
        'module.food.subtitle': 'Restaurantes e refeições',
        'module.groceries.title': 'Mercearia',
        'module.groceries.subtitle': 'Lojas perto de si',
        'module.rides.title': 'Viagens',
        'module.rides.subtitle': 'Chegue rápido',
        'module.package.title': 'Enviar Encomenda',
        'module.package.subtitle': 'Entrega courier',
        'module.car_rental.title': 'Aluguer de Carro',
        'module.car_rental.subtitle': 'Alugue um veículo',
        'module.doctors.title': 'Médicos',
        'module.doctors.subtitle': 'Marcar consultas',
        'module.services.title': 'Serviços',
        'module.services.subtitle': 'Profissionais locais',
        'module.accommodation.title': 'Alojamento',
        'module.accommodation.subtitle': 'Reservar estadia',
        'module.property.title': 'Imóveis',
        'module.property.subtitle': 'Arrendar ou comprar',
        'module.wallet.title': 'Carteira',
        'module.wallet.subtitle': 'Pagar e gerir dinheiro',
        'module.business.title': 'Empresas',
        'module.business.subtitle': 'Contas corporativas',
    },
    'fr': {
        'app.tagline': 'Votre vie, une seule app',
        'home.greeting': "De quoi avez-vous besoin aujourd'hui?",
        'module.food.title': 'Nourriture',
        'module.food.subtitle': 'Restaurants et repas',
        'module.doctors.title': 'Médecins',
        'module.doctors.subtitle': 'Prendre rendez-vous',
    },
    'es': {
        'app.tagline': 'Tu vida, una app',
        'home.greeting': '¿Qué necesitas hoy?',
        'module.food.title': 'Comida',
        'module.food.subtitle': 'Restaurantes y comidas',
        'module.doctors.title': 'Médicos',
        'module.doctors.subtitle': 'Reservar consultas',
    },
}


class Command(BaseCommand):
    help = 'Seed Kudya super-app platform data'

    def handle(self, *args, **options):
        for name, code, currency, tz in COUNTRIES:
            country, _ = Country.objects.update_or_create(
                code=code,
                defaults={'name': name, 'currency': currency, 'timezone': tz, 'is_active': True},
            )
            if code == 'ZA':
                for city_name in ['Johannesburg', 'Cape Town', 'Durban', 'Pretoria']:
                    City.objects.get_or_create(country=country, name=city_name)
            if code == 'MZ':
                for city_name in ['Maputo', 'Matola', 'Beira']:
                    City.objects.get_or_create(country=country, name=city_name)

        for key, route, icon, gs, ge, order in MODULES:
            PlatformModule.objects.update_or_create(
                key=key,
                defaults={
                    'route': route,
                    'icon': icon,
                    'gradient_start': gs,
                    'gradient_end': ge,
                    'order': order,
                    'is_active': True,
                },
            )

        for slug, name, order in SPECIALTIES:
            MedicalSpecialty.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'order': order, 'is_active': True},
            )

        for lang, translations in HOME_TRANSLATIONS.items():
            for key, value in translations.items():
                Translation.objects.update_or_create(
                    key=key,
                    language=lang,
                    module='home',
                    defaults={'value': value, 'is_active': True},
                )

        try:
            from pricing.models import PricingRule
            za = Country.objects.filter(code='ZA').first()
            if za:
                PricingRule.objects.get_or_create(
                    service_type='ride',
                    ride_type='economy',
                    country=za,
                    defaults={
                        'base_fare': 25,
                        'per_km_rate': 8,
                        'per_minute_rate': 1.5,
                        'minimum_fare': 35,
                        'is_active': True,
                    },
                )
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS('Super-app seed data created successfully.'))
