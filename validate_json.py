import json

with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for obj in data:
    if obj.get("model", "").startswith("products."):
        obj["model"] = obj["model"].replace("products.", "stores.")

with open("products_fixed.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done! Use 'products_fixed.json' to load your data.")
