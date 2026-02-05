"""
Django management command to seed the database with real data for testing.
Inserts ALL data types the platform uses: users, stores, products, properties,
customers, drivers, orders, services, careers, info, currency, etc.
Run as real user: python manage.py seed_data
"""
import os
from io import BytesIO
from decimal import Decimal
from datetime import timedelta, datetime, time
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
            def safe_delete(qs, label=""):
                try:
                    count = qs.count()
                    if count:
                        qs.delete()
                        self.stdout.write(f"  Cleared {label}: {count}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  {label} clear: {e}"))

            try:
                from order.models import OrderDetails, Order
                safe_delete(OrderDetails.objects.filter(order__customer__user__username__startswith="seed_"), "OrderDetails")
                safe_delete(Order.objects.filter(customer__user__username__startswith="seed_"), "Orders")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Orders clear: {e}"))

            try:
                from properties.models import Property, PropertyImage
                safe_delete(PropertyImage.objects.filter(property__owner__username__startswith="seed_"), "PropertyImages")
                safe_delete(Property.objects.filter(owner__username__startswith="seed_"), "Properties")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Properties clear: {e}"))

            try:
                from services.models import Booking, Service
                safe_delete(Booking.objects.filter(customer__user__username__startswith="seed_"), "Bookings")
                safe_delete(Service.objects.filter(parceiro__name__startswith="[Seed]"), "Services")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Services clear: {e}"))

            try:
                from careers.models import Career, JobApplication
                safe_delete(JobApplication.objects.filter(career__title__startswith="[Seed]"), "JobApplications")
                safe_delete(Career.objects.filter(title__startswith="[Seed]"), "Careers")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Careers clear: {e}"))

            safe_delete(Product.objects.filter(store__name__startswith="[Seed]"), "Products")
            safe_delete(Store.objects.filter(name__startswith="[Seed]"), "Stores")
            safe_delete(AboutUs.objects.filter(title__startswith="[Seed]"), "AboutUs")
            safe_delete(User.objects.filter(username__startswith="seed_"), "Users")

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
            obj, _ = ExchangeRate.objects.update_or_create(
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
                            description=f"<p>{desc}</p>",
                            stock=50,
                        )
                    self.stdout.write("  - Products created")

        # 7. Properties (rent daily, rent monthly, buy) - Airbnb-style
        try:
            from properties.models import Property
            prop_owner, _ = User.objects.get_or_create(
                username="seed_property_owner",
                defaults={
                    "email": "property@kudya.shop",
                    "first_name": "Property",
                    "last_name": "Owner",
                    "is_staff": False,
                }
            )
            if _:
                prop_owner.set_password("seedpass123")
                prop_owner.save()

            properties_data = [
                ("Apartamento no centro de Luanda", "rent_daily", "apartment", 15000, "Luanda", 2, 1, ["wifi", "parking"]),
                ("Casa com vista para o mar", "rent_monthly", "house", 350000, "Benguela", 4, 3, ["wifi", "pool", "parking"]),
                ("Estúdio para venda", "buy", "studio", 25000000, "Luanda", 1, 1, ["wifi"]),
            ]
            for title, lt, pt, price, city, beds, baths, amenities in properties_data:
                Property.objects.get_or_create(
                    owner=prop_owner,
                    title=title,
                    defaults={
                        "description": f"<p>Excelente {title.lower()}.</p>",
                        "address": f"Rua Principal, {city}",
                        "city": city,
                        "listing_type": lt,
                        "property_type": pt,
                        "price": Decimal(price),
                        "bedrooms": beds,
                        "bathrooms": baths,
                        "amenities": amenities,
                        "is_available": True,
                        "is_approved": True,
                    }
                )
            self.stdout.write("  - Properties created (rent_daily, rent_monthly, buy)")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Properties: {e}"))

        # 8. Customer + Driver users
        cust_user, cust_created = User.objects.get_or_create(
            username="seed_customer",
            defaults={"email": "customer@kudya.shop", "first_name": "Seed", "last_name": "Customer", "is_customer": True}
        )
        if cust_created:
            cust_user.set_password("seedpass123")
            cust_user.save()

        try:
            from customers.models import Customer
            Customer.objects.get_or_create(
                user=cust_user,
                defaults={"phone": "+244 900 333 444", "address": "Luanda, Angola"}
            )
            self.stdout.write("  - Customer created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Customer: {e}"))

        drv_user, drv_created = User.objects.get_or_create(
            username="seed_driver",
            defaults={"email": "driver@kudya.shop", "first_name": "Seed", "last_name": "Driver", "is_driver": True}
        )
        if drv_created:
            drv_user.set_password("seedpass123")
            drv_user.save()

        try:
            from drivers.models import Driver
            Driver.objects.get_or_create(
                user=drv_user,
                defaults={
                    "phone": "+244 900 555 666",
                    "vehicle_type": "motorcycle",
                    "plate": "LD-00-00-AA",
                    "is_online": True,
                    "is_available": True,
                }
            )
            self.stdout.write("  - Driver created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Driver: {e}"))

        # 9. Orders (real orders like a customer would place)
        try:
            from order.models import Order, OrderDetails
            from customers.models import Customer
            cust = Customer.objects.filter(user__username="seed_customer").first()
            seed_store = Store.objects.filter(name__startswith="[Seed]").first()
            prod = Product.objects.filter(store=seed_store).first() if seed_store else None

            if cust and seed_store and prod:
                order, o_created = Order.objects.get_or_create(
                    customer=cust,
                    store=seed_store,
                    delivery_notes="[Seed] Test order",
                    defaults={
                        "address": "Av. 4 de Fevereiro, Luanda",
                        "total": Decimal("3500"),
                        "delivery_fee": Decimal("500"),
                        "discount_amount": Decimal("0"),
                        "original_price": Decimal("3000"),
                        "status": Order.PROCESSING,
                        "payment_method": "cash",
                    }
                )
                if o_created:
                    OrderDetails.objects.create(order=order, product=prod, quantity=1, sub_total=prod.price)
                    self.stdout.write("  - Order created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Order: {e}"))

        # 10. Services (ServiceCategory, Service, Booking)
        try:
            from services.models import ServiceCategory, Service, Booking
            from customers.models import Customer

            sc, _ = ServiceCategory.objects.get_or_create(
                slug="health",
                defaults={
                    "name": "Health & Medical",
                    "name_pt": "Saúde e Medicina",
                    "category_type": "health",
                    "description": "Health services",
                }
            )
            seed_store = Store.objects.filter(name__startswith="[Seed]").first()
            cust = Customer.objects.filter(user__username="seed_customer").first()
            if seed_store and cust:
                svc, _ = Service.objects.get_or_create(
                    parceiro=seed_store,
                    category=sc,
                    title="Consultation",
                    defaults={
                        "title_pt": "Consulta",
                        "description": "General health consultation",
                        "price": Decimal("5000"),
                        "duration_minutes": 60,
                        "delivery_type": "in_person",
                        "is_active": True,
                    }
                )
                book_date = timezone.now().date() + timedelta(days=2)
                Booking.objects.get_or_create(
                    service=svc,
                    customer=cust,
                    booking_date=book_date,
                    booking_time=datetime.strptime("10:00", "%H:%M").time(),
                    defaults={
                        "duration_minutes": 60,
                        "price": Decimal("5000"),
                        "status": "confirmed",
                        "payment_status": "paid",
                    }
                )
                self.stdout.write("  - Services & Booking created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Services: {e}"))

        # 11. Careers & JobApplication
        try:
            from careers.models import Career, JobApplication
            care, _ = Career.objects.get_or_create(
                title="[Seed] Developer",
                defaults={
                    "location": "Luanda",
                    "description": "<p>Full-stack developer needed.</p>",
                    "requirements": "Python, JavaScript, Django",
                }
            )
            JobApplication.objects.get_or_create(
                career=care,
                full_name="João Silva",
                email="joao@test.com",
                defaults={
                    "cover_letter": "Interested in this position.",
                    "status": "submitted",
                    "resume": ContentFile(b"Resume content for seed", name="resume.txt"),
                }
            )
            self.stdout.write("  - Careers & JobApplication created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Careers: {e}"))

        # 12. Why_Choose_Us, Team, Contact
        try:
            from info.models import Why_Choose_Us, Team, Contact
            Why_Choose_Us.objects.get_or_create(
                title="[Seed] Quality",
                defaults={"content": "We deliver quality products and services."}
            )
            Team.objects.get_or_create(
                name="[Seed] Maria",
                defaults={
                    "title": "CEO",
                    "bio": "Leading the team.",
                    "image": ContentFile(MINIMAL_PNG, name="team.png"),
                }
            )
            Contact.objects.get_or_create(
                subject="[Seed] Test contact",
                email="contact@test.com",
                defaults={
                    "phone": "+244 900 000 000",
                    "message": "This is a test message.",
                }
            )
            self.stdout.write("  - Why_Choose_Us, Team, Contact created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Info extras: {e}"))

        # 13. Extra store types (Grocery, Pharmacy) and products
        try:
            grocery_cat = StoreCategory.objects.filter(slug="supermercados").first()
            pharm_cat = StoreCategory.objects.filter(slug="farmacias").first()
            grocery_type = StoreType.objects.filter(name="Grocery").first()
            pharm_type = StoreType.objects.filter(name="Pharmacy").first()

            if grocery_cat and grocery_type:
                u2, _ = User.objects.get_or_create(
                    username="seed_grocery_owner",
                    defaults={"email": "grocery@kudya.shop", "first_name": "Grocery", "last_name": "Owner"}
                )
                if _:
                    u2.set_password("seedpass123")
                    u2.save()
                Store.objects.get_or_create(
                    user=u2,
                    defaults={
                        "name": "[Seed] Supermercado Central",
                        "phone": "+244 900 777 888",
                        "address": "Maianga, Luanda",
                        "logo": ContentFile(MINIMAL_PNG, name="grocery_logo.png"),
                        "category": grocery_cat,
                        "store_type": grocery_type,
                        "is_approved": True,
                    }
                )
                self.stdout.write("  - Grocery store created")

            if pharm_cat and pharm_type:
                u3, _ = User.objects.get_or_create(
                    username="seed_pharmacy_owner",
                    defaults={"email": "pharmacy@kudya.shop", "first_name": "Pharmacy", "last_name": "Owner"}
                )
                if _:
                    u3.set_password("seedpass123")
                    u3.save()
                Store.objects.get_or_create(
                    user=u3,
                    defaults={
                        "name": "[Seed] Farmácia Popular",
                        "phone": "+244 900 999 000",
                        "address": "Centro, Luanda",
                        "logo": ContentFile(MINIMAL_PNG, name="pharm_logo.png"),
                        "category": pharm_cat,
                        "store_type": pharm_type,
                        "is_approved": True,
                    }
                )
                self.stdout.write("  - Pharmacy store created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Extra stores: {e}"))

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))
