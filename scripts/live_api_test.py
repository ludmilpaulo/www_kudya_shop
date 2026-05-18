#!/usr/bin/env python3
"""Live API smoke tests for Kudya super-app (local + production)."""
import json
import sys
import time
import urllib.error
import urllib.request

BASES = [
    ("LOCAL", "http://127.0.0.1:8765"),
    ("PRODUCTION", "https://www.kudya.store"),
]


def request(base, method, path, token=None, data=None, timeout=15):
    url = f"{base.rstrip('/')}{path}"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed = raw[:200]
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw[:200]
        return e.code, parsed
    except Exception as e:
        return 0, str(e)


def check(name, status, ok_range=(200, 299)):
    lo, hi = ok_range
    ok = lo <= status < hi
    mark = "PASS" if ok else "FAIL"
    preview = ""
    print(f"{mark} [{status}] {name}{preview}")
    return ok


def run_suite(label, base):
    print(f"\n{'=' * 60}\n{label} — {base}\n{'=' * 60}")
    fails = 0

    cases = [
        ("Home modules", "GET", "/api/platform/home-modules/"),
        ("Translations EN", "GET", "/api/translations/?lang=en&module=home"),
        ("Doctor specialties", "GET", "/api/doctors/specialties/"),
        ("Countries", "GET", "/api/countries/"),
        ("Rental vehicles", "GET", "/api/rentals/vehicles/"),
        ("Accommodation listings", "GET", "/api/accommodation/listings/"),
        ("Store list (legacy)", "GET", "/store/"),
    ]
    for name, method, path in cases:
        status, _ = request(base, method, path)
        if not check(name, status):
            fails += 1

    email = f"livetest_{int(time.time())}@kudya.test"
    status, body = request(
        base,
        "POST",
        "/api/auth/register/",
        data={"email": email, "password": "TestPass123!", "first_name": "Live", "last_name": "Test"},
    )
    token = None
    if status == 201 and isinstance(body, dict):
        token = body.get("token")
        print(f"PASS [201] Register — {email}")
    else:
        print(f"FAIL [{status}] Register — {body}")
        fails += 1

    if not token:
        print(f"---------- {label}: {fails} failure(s) (no token) ----------")
        return fails

    authed = [
        ("Auth me", "GET", "/api/auth/me/"),
        (
            "Ride estimate",
            "POST",
            "/api/rides/estimate/",
            {
                "pickup_lat": -26.2041,
                "pickup_lng": 28.0473,
                "destination_lat": -26.1076,
                "destination_lng": 28.0567,
                "ride_type": "economy",
            },
        ),
        (
            "Ride request",
            "POST",
            "/api/rides/request/",
            {
                "pickup_lat": -26.2041,
                "pickup_lng": 28.0473,
                "pickup_address": "Sandton",
                "destination_lat": -26.1076,
                "destination_lng": 28.0567,
                "destination_address": "OR Tambo",
                "ride_type": "economy",
            },
        ),
        ("Ride history", "GET", "/api/rides/history/"),
        (
            "Package delivery",
            "POST",
            "/api/deliveries/",
            {
                "pickup_address": "A",
                "dropoff_address": "B",
                "pickup_lat": -26.2,
                "pickup_lng": 28.0,
                "dropoff_lat": -26.1,
                "dropoff_lng": 28.1,
                "package_type": "small",
                "recipient_name": "Test",
                "recipient_phone": "+27123456789",
            },
        ),
        ("Wallet", "GET", "/api/wallet/"),
        ("Support tickets", "GET", "/api/support/"),
    ]
    for item in authed:
        name, method, path = item[0], item[1], item[2]
        data = item[3] if len(item) > 3 else None
        status, body = request(base, method, path, token=token, data=data)
        if not check(name, status):
            fails += 1
            if isinstance(body, dict):
                print(f"       → {body}")

    print(f"---------- {label}: {fails} failure(s) ----------")
    return fails


def main():
    total = 0
    for label, base in BASES:
        try:
            total += run_suite(label, base)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"ERROR running {label}: {e}")
            total += 1
    print(f"\nTOTAL FAILURES: {total}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
