#!/usr/bin/env python
"""
Standalone script to seed the database. Run from project root:
  python run_seed.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "www_kudya_shop.settings")
django.setup()

from decimal import Decimal
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

MINIMAL_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
    0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
    0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
    0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
])


def main():
    from stores.models import Store, StoreType, StoreCategory, Product, ProductCategory, OpeningHour
    from currency.models import ExchangeRate
    from info.models import AboutUs

    print("Seeding data...")

    # Store Types
    for name, desc in [("Restaurant", "Food and dining"), ("Grocery", "Supermarket"), ("Pharmacy", "Health")]:
        StoreType.objects.get_or_create(name=name, defaults={"description": desc})
    print("  - Store types OK")

    # Store Categories
    for slug, name in [("restaurantes", "Restaurantes"), ("supermercados", "Supermercados")]:
        StoreCategory.objects.get_or_create(slug=slug, defaults={"name": name})
    print("  - Store categories OK")

    # Product Categories
    for name in ["Refeições", "Bebidas", "Snacks"]:
        ProductCategory.objects.get_or_create(name=name, defaults={"icon": "th-large"})
    print("  - Product categories OK")

    # Exchange Rates
    today = timezone.now().date()
    for curr, rate in [("USD", "0.0012"), ("EUR", "0.0011"), ("ZAR", "0.022")]:
        ExchangeRate.objects.update_or_create(
            base_currency="AOA", target_currency=curr, date=today,
            defaults={"rate": Decimal(rate)}
        )
    print("  - Exchange rates OK")

    # About Us
    AboutUs.objects.get_or_create(
        title="[Seed] Kudya",
        defaults={
            "about": "<p>Kudya - Your trusted marketplace.</p>",
            "address": "Luanda, Angola",
            "phone": "+244 900 000 000",
            "email": "contact@kudya.shop",
        }
    )
    print("  - About Us OK")

    # Sample properties (rent daily/monthly, buy)
    try:
        from properties.models import Property
        from django.contrib.auth import get_user_model
        User = get_user_model()
        prop_user, _ = User.objects.get_or_create(
            username="seed_property_owner",
            defaults={"email": "property@kudya.shop", "first_name": "Property", "last_name": "Owner"}
        )
        if not prop_user.has_usable_password():
            prop_user.set_password("seedpass123")
            prop_user.save()

        if not Property.objects.filter(title__startswith="[Seed]").exists():
            Property.objects.create(
                owner=prop_user,
                title="[Seed] Cozy Apartment - Luanda",
                description="Beautiful 2-bedroom apartment in the heart of Luanda. Perfect for short stays.",
                address="Maianga, Luanda",
                city="Luanda",
                listing_type="rent_daily",
                property_type="apartment",
                price=Decimal("15000"),
                bedrooms=2,
                bathrooms=1,
                area_sqm=75,
                amenities=["wifi", "parking", "ac"],
                is_available=True,
                is_approved=True,
            )
            Property.objects.create(
                owner=prop_user,
                title="[Seed] Villa for Monthly Rent",
                description="Spacious villa with garden. Ideal for families.",
                address="Talatona, Luanda",
                city="Luanda",
                listing_type="rent_monthly",
                property_type="villa",
                price=Decimal("350000"),
                bedrooms=4,
                bathrooms=3,
                area_sqm=200,
                amenities=["wifi", "parking", "pool", "garden"],
                is_available=True,
                is_approved=True,
            )
            Property.objects.create(
                owner=prop_user,
                title="[Seed] Studio for Sale",
                description="Modern studio apartment, ready to move in.",
                address="Centro, Luanda",
                city="Luanda",
                listing_type="buy",
                property_type="studio",
                price=Decimal("25000000"),
                bedrooms=1,
                bathrooms=1,
                area_sqm=45,
                amenities=["wifi", "security"],
                is_available=True,
                is_approved=True,
            )
            print("  - Sample properties OK")
    except Exception as e:
        print(f"  - Properties skipped ({e})")

    # Store + Products
    user, _ = User.objects.get_or_create(
        username="seed_store_owner",
        defaults={"email": "store@kudya.shop", "first_name": "Seed", "last_name": "Owner"}
    )
    if user.password == "!" or not user.has_usable_password():
        user.set_password("seedpass123")
        user.save()

    store_cat = StoreCategory.objects.get(slug="restaurantes")
    store_type = StoreType.objects.get(name="Restaurant")
    logo_file = ContentFile(MINIMAL_PNG, name="seed_logo.png")

    store, created = Store.objects.get_or_create(
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
    if created:
        for day in range(1, 6):
            OpeningHour.objects.get_or_create(store=store, day=day, defaults={
                "from_hour": "08:00 AM", "to_hour": "10:00 PM", "is_closed": False
            })
        prod_cat = ProductCategory.objects.get(name="Refeições")
        for pname, price, desc in [
            ("Frango Grelhado", 2500, "Frango com arroz"),
            ("Mufete", 1800, "Peixe grelhado"),
            ("Sumo de Manga", 500, "Sumo natural"),
        ]:
            Product.objects.create(name=pname, store=store, category=prod_cat, price=Decimal(str(price)), description=desc, stock=50)
        print("  - Store and products OK")
    else:
        print("  - Store already exists")

    print("Done.")


if __name__ == "__main__":
    main()
