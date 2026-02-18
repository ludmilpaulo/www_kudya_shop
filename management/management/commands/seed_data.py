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
                from drivers.models import DeliveryRequest, DriverRating
                from stores.models.product import Wishlist, Review
                from info.models import Carousel
                safe_delete(DriverRating.objects.filter(driver__user__username__startswith="seed_"), "DriverRatings")
                safe_delete(DeliveryRequest.objects.filter(order__customer__user__username__startswith="seed_"), "DeliveryRequests")
                safe_delete(OrderDetails.objects.filter(order__customer__user__username__startswith="seed_"), "OrderDetails")
                safe_delete(Order.objects.filter(customer__user__username__startswith="seed_"), "Orders")
                safe_delete(Wishlist.objects.filter(user__username__startswith="seed_"), "Wishlist")
                safe_delete(Review.objects.filter(user__username__startswith="seed_"), "Reviews")
                safe_delete(Carousel.objects.filter(title__startswith="[Seed]"), "Carousel")
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

        # 5b. Admin user
        admin_user, admin_created = User.objects.get_or_create(
            username="seed_admin",
            defaults={"email": "admin@kudya.shop", "first_name": "Admin", "last_name": "Kudya", "is_staff": True, "is_superuser": True}
        )
        if admin_created:
            admin_user.set_password("seedpass123")
            admin_user.save()
            self.stdout.write("  - Admin user created (seed_admin / seedpass123)")

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
                prod_cat_ref = ProductCategory.objects.filter(name="Refeições").first()
                prod_cat_beb = ProductCategory.objects.filter(name="Bebidas").first()
                prod_cat_snack = ProductCategory.objects.filter(name="Snacks").first()
                if prod_cat_ref:
                    products_data = [
                        ("Frango Grelhado", 2500, "Frango grelhado com arroz e salada", prod_cat_ref),
                        ("Mufete", 1800, "Peixe grelhado com funje e banana", prod_cat_ref),
                        ("Calulu", 2200, "Carne seca com quiabo e óleo de palma", prod_cat_ref),
                        ("Moamba de Galinha", 2400, "Galinha em molho de dendém", prod_cat_ref),
                        ("Sumo de Manga", 500, "Sumo natural", prod_cat_beb or prod_cat_ref),
                        ("Cerveja Cuca", 600, "Cerveja nacional", prod_cat_beb or prod_cat_ref),
                        ("Água Mineral", 250, "Água 500ml", prod_cat_beb or prod_cat_ref),
                        ("Cachupa", 1500, "Pequeno-almoço tradicional", prod_cat_snack or prod_cat_ref),
                    ]
                    for pname, price, desc, cat in products_data:
                        Product.objects.get_or_create(name=pname, store=store, defaults={"category": cat, "price": Decimal(price), "description": f"<p>{desc}</p>", "stock": 50})
                    self.stdout.write("  - Restaurant products created")

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

        # 8. Customer + Driver users (multiple)
        customers_data = [
            ("seed_customer", "customer@kudya.shop", "Maria", "Santos", "+244 900 333 444", "Av. 4 de Fevereiro, Luanda"),
            ("seed_customer2", "ana@kudya.shop", "Ana", "Costa", "+244 901 111 222", "Maianga, Luanda"),
            ("seed_customer3", "carlos@kudya.shop", "Carlos", "Ferreira", "+244 902 222 333", "Centro, Luanda"),
        ]
        try:
            from customers.models import Customer
            for uname, email, fname, lname, phone, addr in customers_data:
                u, created = User.objects.get_or_create(username=uname, defaults={"email": email, "first_name": fname, "last_name": lname, "is_customer": True})
                if created:
                    u.set_password("seedpass123")
                    u.save()
                Customer.objects.get_or_create(user=u, defaults={"phone": phone, "address": addr})
            self.stdout.write(f"  - {len(customers_data)} customers created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Customer: {e}"))

        drivers_data = [
            ("seed_driver", "driver@kudya.shop", "João", "Mendes", "motorcycle", "LD-00-00-AA", "+244 900 555 666"),
            ("seed_driver2", "manuel@kudya.shop", "Manuel", "Rodrigues", "car", "LD-11-11-BB", "+244 901 666 777"),
        ]
        try:
            from drivers.models import Driver
            for uname, email, fname, lname, vtype, plate, phone in drivers_data:
                u, created = User.objects.get_or_create(username=uname, defaults={"email": email, "first_name": fname, "last_name": lname, "is_driver": True})
                if created:
                    u.set_password("seedpass123")
                    u.save()
                Driver.objects.get_or_create(user=u, defaults={"phone": phone, "vehicle_type": vtype, "plate": plate, "is_online": True, "is_available": True, "is_verified": True})
            self.stdout.write(f"  - {len(drivers_data)} drivers created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Driver: {e}"))

        # 9. Orders (multiple, various statuses)
        try:
            from order.models import Order, OrderDetails
            from customers.models import Customer
            from drivers.models import Driver
            seed_stores = list(Store.objects.filter(name__startswith="[Seed]"))
            seed_customers = list(Customer.objects.filter(user__username__startswith="seed_").filter(user__is_customer=True))
            seed_drivers = list(Driver.objects.filter(user__username__startswith="seed_"))
            orders_created = 0
            for i, cust in enumerate(seed_customers[:3]):
                for store in seed_stores[:2]:
                    prods = list(Product.objects.filter(store=store)[:2])
                    if not prods:
                        continue
                    prod, qty = prods[0], 1 + (i % 2)
                    sub = prod.price * qty
                    statuses = [Order.PROCESSING, Order.READY, Order.ONTHEWAY, Order.DELIVERED]
                    status = statuses[i % len(statuses)]
                    drv = seed_drivers[i % len(seed_drivers)] if seed_drivers and status in (Order.ONTHEWAY, Order.DELIVERED) else None
                    order, o_created = Order.objects.get_or_create(
                        customer=cust,
                        store=store,
                        address=cust.address or "Luanda",
                        delivery_notes=f"[Seed] Order from {cust.user.get_full_name()}",
                        defaults={
                            "total": sub, "delivery_fee": Decimal("500"), "discount_amount": Decimal("0"),
                            "original_price": sub, "status": status, "payment_method": "cash" if i % 2 == 0 else "card",
                            "driver": drv,
                        }
                    )
                    if o_created:
                        OrderDetails.objects.get_or_create(order=order, product=prod, defaults={"quantity": qty, "sub_total": sub})
                        orders_created += 1
            if orders_created:
                self.stdout.write(f"  - {orders_created} orders created")
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
                u2, u2c = User.objects.get_or_create(username="seed_grocery_owner", defaults={"email": "grocery@kudya.shop", "first_name": "Grocery", "last_name": "Owner"})
                if u2c:
                    u2.set_password("seedpass123")
                    u2.save()
                gstore, gs_c = Store.objects.get_or_create(user=u2, defaults={"name": "[Seed] Supermercado Central", "phone": "+244 900 777 888", "address": "Maianga, Luanda", "logo": ContentFile(MINIMAL_PNG, name="grocery_logo.png"), "category": grocery_cat, "store_type": grocery_type, "is_approved": True})
                if gs_c:
                    for d in range(1, 6):
                        OpeningHour.objects.get_or_create(store=gstore, day=d, defaults={"from_hour": "07:00 AM", "to_hour": "21:00 PM", "is_closed": False})
                prod_cat_sn = ProductCategory.objects.filter(name="Snacks").first()
                if gstore and prod_cat_sn:
                    for pname, price, desc in [("Arroz Nacional 5kg", 3500, "Arroz"), ("Feijão 1kg", 1200, "Feijão"), ("Óleo Palma 1L", 800, "Óleo"), ("Leite 1L", 600, "Leite"), ("Pão de Forma", 450, "Pão")]:
                        Product.objects.get_or_create(name=pname, store=gstore, defaults={"category": prod_cat_sn, "price": Decimal(price), "description": f"<p>{desc}</p>", "stock": 100})
                self.stdout.write("  - Grocery store + products created")

            if pharm_cat and pharm_type:
                u3, u3c = User.objects.get_or_create(username="seed_pharmacy_owner", defaults={"email": "pharmacy@kudya.shop", "first_name": "Pharmacy", "last_name": "Owner"})
                if u3c:
                    u3.set_password("seedpass123")
                    u3.save()
                pstore, ps_c = Store.objects.get_or_create(user=u3, defaults={"name": "[Seed] Farmácia Popular", "phone": "+244 900 999 000", "address": "Centro, Luanda", "logo": ContentFile(MINIMAL_PNG, name="pharm_logo.png"), "category": pharm_cat, "store_type": pharm_type, "is_approved": True})
                if ps_c:
                    for d in range(1, 7):
                        OpeningHour.objects.get_or_create(store=pstore, day=d, defaults={"from_hour": "08:00 AM", "to_hour": "20:00 PM", "is_closed": False})
                prod_cat_hi = ProductCategory.objects.filter(name="Higiene").first()
                if pstore and prod_cat_hi:
                    for pname, price, desc in [("Paracetamol 500mg", 350, "Analgésico"), ("Ibuprofeno 400mg", 450, "Anti-inflamatório"), ("Soro Fisiológico", 250, "Limpagem"), ("Vitamina C", 1200, "Suplemento"), ("Máscaras 10un", 800, "Proteção")]:
                        Product.objects.get_or_create(name=pname, store=pstore, defaults={"category": prod_cat_hi, "price": Decimal(price), "description": f"<p>{desc}</p>", "stock": 80})
                self.stdout.write("  - Pharmacy store + products created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Extra stores: {e}"))

        # 14. Reviews & Wishlist
        try:
            from stores.models.product import Review, Wishlist
            for u in User.objects.filter(username__startswith="seed_customer")[:2]:
                for p in Product.objects.filter(store__name__startswith="[Seed]")[:4]:
                    Review.objects.get_or_create(user=u, product=p, defaults={"rating": 4 + (abs(hash(str(u.pk) + str(p.pk))) % 2), "comment": f"Ótimo! - {u.get_full_name()}"})
                for p in Product.objects.filter(store__name__startswith="[Seed]")[4:7]:
                    Wishlist.objects.get_or_create(user=u, product=p)
            self.stdout.write("  - Reviews & Wishlist created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Reviews/Wishlist: {e}"))

        # 15. Coupons
        try:
            from order.models import Coupon
            for u in User.objects.filter(username__in=["seed_customer", "seed_customer2"]):
                Coupon.objects.get_or_create(user=u, defaults={"code": f"SEED_{u.username.upper()}", "discount_percentage": Decimal("5"), "order_count": 0})
            self.stdout.write("  - Coupons created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Coupons: {e}"))

        # 16. Carousel
        try:
            from info.models import Carousel, Image as CarouselImage
            car, c_created = Carousel.objects.get_or_create(title="[Seed] Kudya", defaults={"sub_title": "Food, Groceries & More"})
            if c_created or not car.image.exists():
                img = CarouselImage.objects.create(image=ContentFile(MINIMAL_PNG, name="carousel1.png"))
                car.image.add(img)
            self.stdout.write("  - Carousel created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Carousel: {e}"))

        # 17. More careers
        try:
            from careers.models import Career, JobApplication
            for title, loc, req in [("[Seed] Marketing Manager", "Luanda", "3+ years"), ("[Seed] Customer Support", "Remote", "Portuguese & English")]:
                c, _ = Career.objects.get_or_create(title=title, defaults={"location": loc, "description": "<p>Join our team.</p>", "requirements": req})
                JobApplication.objects.get_or_create(career=c, full_name="Ana Souza", email="ana@test.com", defaults={"cover_letter": "Interested", "status": "submitted", "resume": ContentFile(b"CV", name="cv.txt")})
            self.stdout.write("  - More careers created")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Careers: {e}"))

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))
