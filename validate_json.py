import json
import random

NUM_STORES = 600
PRODUCTS_PER_STORE = 10
NUM_CATEGORIES = 10   # 1–10
NUM_SIZES = 5         # 1–5
NUM_COLORS = 5        # 1–5
NUM_IMAGES = 20       # 1–20

seasons = ["summer", "winter", "all_seasons"]
genders = ["unisex", "male", "female"]

fixture = []
pk = 1

for store_id in range(1, NUM_STORES + 1):
    for n in range(PRODUCTS_PER_STORE):
        # Category, images, sizes, colors (cycle for variety)
        category = (n % NUM_CATEGORIES) + 1
        sizes = [((n + i) % NUM_SIZES) + 1 for i in range(2)]
        colors = [((n + i) % NUM_COLORS) + 1 for i in range(2)]
        images = [((n + i) % NUM_IMAGES) + 1 for i in range(2)]

        product = {
            "model": "stores.product",
            "pk": pk,
            "fields": {
                "name": f"Product {n+1} for Store {store_id}",
                "store": store_id,
                "description": f"This is Product {n+1} for Store {store_id}. High quality, best seller.",
                "price": f"{random.randint(10, 500)}.{random.randint(0,99):02d}",
                "category": category,
                "stock": random.randint(5, 100),
                "on_sale": random.choice([True, False]),
                "percentage": f"{random.randint(0, 15)}.{random.randint(0,9)}",
                "bulk_sale": random.choice([True, False]),
                "discount_percentage": random.choice([0, 10, 15, 20]),
                "season": random.choice(seasons),
                "gender": random.choice(genders),
                "images": images,
                "sizes": sizes,
                "colors": colors
            }
        }
        fixture.append(product)
        pk += 1

with open("products.json", "w") as f:
    json.dump(fixture, f, indent=2)
