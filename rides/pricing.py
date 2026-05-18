"""Ride fare estimation — uses pricing.PricingRule when available."""
from decimal import Decimal
import math


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> Decimal:
    r = 6371
    p = math.pi / 180
    a = (
        0.5 - math.cos((lat2 - lat1) * p) / 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lng2 - lng1) * p)) / 2
    )
    return Decimal(str(round(2 * r * math.asin(math.sqrt(a)), 2)))


def estimate_duration_minutes(distance_km: Decimal) -> int:
    avg_speed = 30  # km/h city average
    return max(5, int(float(distance_km) / avg_speed * 60))


def estimate_ride_price(
    distance_km: Decimal,
    duration_minutes: int,
    ride_type: str = 'economy',
    surge_multiplier: Decimal = Decimal('1'),
    country_code: str = 'ZA',
) -> dict:
    """Return price breakdown from rules or sensible defaults."""
    try:
        from pricing.models import PricingRule
        rule = PricingRule.objects.filter(
            service_type='ride',
            ride_type=ride_type,
            country__code=country_code,
            is_active=True,
        ).first()
        if not rule:
            rule = PricingRule.objects.filter(
                service_type='ride',
                ride_type='economy',
                country__isnull=True,
                is_active=True,
            ).first()
    except Exception:
        rule = None

    if rule:
        base = rule.base_fare
        per_km = rule.per_km_rate
        per_min = rule.per_minute_rate
        minimum = rule.minimum_fare
    else:
        multipliers = {
            'economy': Decimal('1'),
            'comfort': Decimal('1.25'),
            'premium': Decimal('1.6'),
            'xl': Decimal('1.4'),
            'bike': Decimal('0.7'),
            'delivery_bike': Decimal('0.65'),
            'women': Decimal('1.1'),
            'scheduled': Decimal('1.05'),
        }
        mult = multipliers.get(ride_type, Decimal('1'))
        base = Decimal('25') * mult
        per_km = Decimal('8') * mult
        per_min = Decimal('1.5') * mult
        minimum = Decimal('35') * mult

    subtotal = base + (per_km * distance_km) + (per_min * Decimal(duration_minutes))
    total = max(minimum, subtotal) * surge_multiplier
    return {
        'base_fare': str(base),
        'distance_km': str(distance_km),
        'duration_minutes': duration_minutes,
        'per_km': str(per_km),
        'per_minute': str(per_min),
        'surge_multiplier': str(surge_multiplier),
        'estimated_price': str(round(total, 2)),
        'currency': 'ZAR' if country_code == 'ZA' else 'MZN',
    }
