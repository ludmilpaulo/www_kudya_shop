# currency/views.py
import requests
from decimal import Decimal
from django.utils import timezone
from django.views.decorators.cache import cache_page
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import ExchangeRate

# Supported currency codes
SUPPORTED_CURRENCIES = [
    'USD', 'EUR', 'GBP', 'AOA', 'BRL', 'ZAR', 'NGN', 'KES', 'GHS', 'EGP',
    'MZN', 'CVE', 'XOF', 'STN', 'XAF', 'ZWL', 'BWP', 'NAD', 'ZMW'
]

BASE_CURRENCY = 'AOA'  # Angolan Kwanza as base


def fetch_exchange_rates_from_api():
    """Fetch latest exchange rates from external API"""
    try:
        # Using exchangerate-api.com free tier (1500 requests/month)
        # You can also use: fixer.io, currencyapi.com, or openexchangerates.org
        api_url = f"https://api.exchangerate-api.com/v4/latest/{BASE_CURRENCY}"
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'rates' in data:
            return data['rates']
        
        return None
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
        return None


def update_exchange_rates():
    """Update exchange rates in database"""
    rates = fetch_exchange_rates_from_api()
    
    if not rates:
        return False
    
    today = timezone.now().date()
    updated_count = 0
    
    for currency_code in SUPPORTED_CURRENCIES:
        if currency_code in rates and currency_code != BASE_CURRENCY:
            rate_value = rates[currency_code]
            
            # Create or update the rate
            ExchangeRate.objects.update_or_create(
                base_currency=BASE_CURRENCY,
                target_currency=currency_code,
                date=today,
                defaults={'rate': Decimal(str(rate_value))}
            )
            updated_count += 1
    
    # Also store the reverse rates (from other currencies to AOA)
    for currency_code in SUPPORTED_CURRENCIES:
        if currency_code in rates and currency_code != BASE_CURRENCY:
            rate_value = rates[currency_code]
            if rate_value > 0:
                reverse_rate = 1 / Decimal(str(rate_value))
                
                ExchangeRate.objects.update_or_create(
                    base_currency=currency_code,
                    target_currency=BASE_CURRENCY,
                    date=today,
                    defaults={'rate': reverse_rate}
                )
    
    return updated_count > 0


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 60 * 12)  # Cache for 12 hours
def get_exchange_rates(request):
    """
    API endpoint to get all current exchange rates
    GET /api/currency/rates/
    """
    try:
        # Check if rates need updating
        if ExchangeRate.needs_update(BASE_CURRENCY):
            updated = update_exchange_rates()
            if not updated:
                # If update failed, proceed with existing rates
                pass
        
        # Get all latest rates
        rates = {}
        for currency in SUPPORTED_CURRENCIES:
            if currency == BASE_CURRENCY:
                rates[currency] = 1.0
            else:
                rate = ExchangeRate.get_latest_rate(BASE_CURRENCY, currency)
                rates[currency] = float(rate) if rate is not None else 1.0
        
        return Response({
            'base_currency': BASE_CURRENCY,
            'rates': rates,
            'last_updated': timezone.now().isoformat(),
        })
    except Exception as e:
        # Fallback: return minimal rates on error
        return Response({
            'base_currency': BASE_CURRENCY,
            'rates': {c: 1.0 if c == BASE_CURRENCY else 0.001 for c in SUPPORTED_CURRENCIES},
            'last_updated': timezone.now().isoformat(),
            'error': str(e),
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def convert_currency(request):
    """
    API endpoint to convert amount between currencies
    POST /api/currency/convert/
    Body: {
        "amount": 1000,
        "from_currency": "AOA",
        "to_currency": "USD"
    }
    """
    try:
        amount = Decimal(str(request.data.get('amount', 0)))
        from_currency = request.data.get('from_currency', BASE_CURRENCY).upper()
        to_currency = request.data.get('to_currency', 'USD').upper()
        
        if from_currency == to_currency:
            converted_amount = amount
        elif from_currency == BASE_CURRENCY:
            # Convert from base to target
            rate = ExchangeRate.get_latest_rate(BASE_CURRENCY, to_currency)
            converted_amount = amount * Decimal(str(rate))
        elif to_currency == BASE_CURRENCY:
            # Convert from target to base
            rate = ExchangeRate.get_latest_rate(from_currency, BASE_CURRENCY)
            converted_amount = amount * Decimal(str(rate))
        else:
            # Convert via base currency (from -> AOA -> to)
            rate_to_base = ExchangeRate.get_latest_rate(from_currency, BASE_CURRENCY)
            amount_in_base = amount * Decimal(str(rate_to_base))
            rate_from_base = ExchangeRate.get_latest_rate(BASE_CURRENCY, to_currency)
            converted_amount = amount_in_base * Decimal(str(rate_from_base))
        
        return Response({
            'original_amount': float(amount),
            'from_currency': from_currency,
            'to_currency': to_currency,
            'converted_amount': float(converted_amount),
            'rate': float(converted_amount / amount) if amount > 0 else 0,
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def force_update_rates(request):
    """
    Force update exchange rates (admin use)
    POST /api/currency/update/
    """
    try:
        success = update_exchange_rates()
        if success:
            return Response({
                'message': 'Exchange rates updated successfully',
                'timestamp': timezone.now().isoformat()
            })
        else:
            return Response(
                {'error': 'Failed to update exchange rates'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

