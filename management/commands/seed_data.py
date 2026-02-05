"""
Django management command to seed the database with real data for testing.
Ensures web and mobile apps can display stores, products, categories, and currency.
"""
import os
from io import BytesIO
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

# Minimal 1x1 transparent PNG
MINIMAL_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
    0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
    0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
    0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
])


class Command(BaseCommand):
    help = "Seed database with stores, products, categories, exchange rates, and info"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing seed data before seeding',
        )

    def handle(self, *args, **options):
        from stores.models import (
            Store, StoreType, StoreCategory, Product, ProductCategory,
            OpeningHour
        )
        from stores.models.product import Image
        from currency.models import ExchangeRate
        from info.models import AboutUs

        if options.get('clear'):
            self.stdout.write("Clearing existing seed data...")
            Product.objects.filter(store__name__startswith="[Seed]").delete()
            Store.objects.filter(name__startswith="[Seed]").delete()
            AboutUs.objects.filter(title__startswith="[Seed]").delete()

        self.stdout.write("Seeding data...")

        # 1. Store Types
        store_types = [
            ("Restaurant", "Food and dining"),
            ("Grocery", "Supermarket and groceries"),
            ("Pharmacy", "Health and pharmacy"),
        ]
        for name, desc in store_types:
            StoreType.objects.get_or_create(name=name, defaults={"description": desc})
        self.stdout.write("  - Store types created")

        # 2. Store Categories
        store_cats = [
            ("restaurantes", "Restaurantes"),
            ("supermercados", "Supermercados"),
            ("farmacias", "Farmácias"),
        ]
        for slug, name in store_cats:
            StoreCategory.objects.get_or_create(slug=slug, defaults={"name": name})
        self.stdout.write("  - Store categories created")

        # 3. Product Categories
        product_cats = [
            ("refeicoes", "Refeições"),
            ("bebidas", "Bebidas"),
            ("snacks", "Snacks"),
            ("higiene", "Higiene"),
        ]
        for name in product_cats:
            ProductCategory.objects.get_or_create(name=name[1], defaults={"icon": "th-large"})
        self.stdout.write("  - Product categories created")

        # 4. Exchange Rates
        today = timezone.now().date()
        rates_data = [
            ("USD", Decimal("0.0012")),
            ("EUR", Decimal("0.0011")),
            ("ZAR", Decimal("0.022")),
            ("BRL", Decimal("0.006")),
        ]
        for curr, rate in rates_data:
            ExchangeRate.objects.update_or_create(
                base_currency="AOA", target_currency=curr, date=today,
                defaults={"rate": rate}
            )
        self.stdout.write("  - Exchange rates created")

        # 5. About Us (info for mobile/web)
        about, _ = AboutUs.objects.get_or_create(
            title="[Seed] Kudya",
            defaults={
                "about": "<p>Kudya - Your trusted marketplace for food, groceries, and more.</p>",
                "address": "Luanda, Angola",
                "phone": "+244 900 000 000",
                "email": "contact@kudya.shop",
                "facebook": "https://facebook.com/kudya",
                "twitter": "https://twitter.com/kudya",
                "instagram": "https://instagram.com/kudya",
            }
        )
        self.stdout.write("  - About Us created")

        # 6. Store + Products (requires User)
        user, created = User.objects.get_or_create(
            username="seed_store_owner",
            defaults={
                "email": "store@kudya.shop",
                "first_name": "Seed",
                "last_name": "Owner",
                "is_staff": False,
            }
        )
        if created:
            user.set_password("seedpass123")
            user.save()

        store_cat = StoreCategory.objects.filter(slug="restaurantes").first()
        store_type = StoreType.objects.filter(name="Restaurant").first()

        if store_cat and store_type:
            logo_file = ContentFile(MINIMAL_PNG, name="seed_logo.png")
            store, store_created = Store.objects.get_or_create(
                user=user,
                defaults={
                    "name": "[Seed] Kudya Restaurant",
                    "phone": "+244 900 111 222",
                    "address": "Av. 4 de Fevereiro, Luanda",
                    "logo": logo_file,
                    "category": store_cat,
                    "store_type": store_type,
                    "is_approved": True,
                    "banner": True,
                }
            )
            if store_created:
                # Opening hours (Mon-Fri 8am-10pm)
                for day in range(1, 6):
                    OpeningHour.objects.get_or_create(
                        store=store, day=day,
                        defaults={
                            "from_hour": "08:00 AM", "to_hour": "10:00 PM",
                            "is_closed": False,
                        }
                    )
                self.stdout.write("  - Store and opening hours created")

                # Products
                prod_cat = ProductCategory.objects.filter(name="Refeições").first()
                if prod_cat:
                    products_data = [
                        ("Frango Grelhado", 2500, "Frango grelhado com arroz e salada"),
                        ("Mufete", 1800, "Peixe grelhado com funje e banana"),
                        ("Calulu", 2200, "Carne seca com quiabo e óleo de palma"),
                        ("Sumo de Manga", 500, "Sumo natural de manga"),
                    ]
                    for pname, price, desc in products_data:
                        Product.objects.create(
                            name=pname,
                            store=store,
                            category=prod_cat,
                            price=Decimal(str(price)),
                            description=desc,
                            stock=50,
                        )
                    self.stdout.write("  - Products created")

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))
