from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Payment
from .serializers import PaymentSerializer
import requests
import uuid

@api_view(['POST'])
def create_payment(request):
    """
    POST: { email, amount, country, currency }
    Returns: payment_id, payment_url, provider, public_key (if Paystack)
    """
    data = request.data
    email = data.get('email')
    amount = data.get('amount')
    country = data.get('country')
    currency = data.get('currency', 'ZAR')

    if not all([email, amount, country, currency]):
        return Response({"detail": "Missing params"}, status=400)

    # Generate payment link based on country/provider
    payment_url = ""
    provider_reference = ""
    meta = {}

    if country == 'ZA':
        # Paystack: create transaction (docs: https://paystack.com/docs/api/transaction/)
        paystack_url = "https://api.paystack.co/transaction/initialize"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        payload = {
            "email": email,
            "amount": int(float(amount) * 100),  # Paystack expects amount in kobo/cents
            "currency": currency,
            "reference": str(uuid.uuid4()),
        }
        response = requests.post(paystack_url, headers=headers, json=payload)
        resp_json = response.json()
        if resp_json.get("status") and resp_json.get("data", {}).get("authorization_url"):
            payment_url = resp_json["data"]["authorization_url"]
            provider_reference = resp_json["data"]["reference"]
            meta = resp_json["data"]
        else:
            return Response({"detail": "Failed to create Paystack payment", "resp": resp_json}, status=400)
        public_key = settings.PAYSTACK_PUBLIC_KEY
    elif country == 'AO':
        # Multicaixa Express (mock, since real requires contract and API docs)
        # You should integrate with Multicaixa REST API here
        provider_reference = str(uuid.uuid4())
        payment_url = f"https://sandbox.multicaixaexpress.ao/pay/{provider_reference}"  # Demo/mock
        public_key = None
    elif country == 'MZ':
        # Mpesa (mock)
        provider_reference = str(uuid.uuid4())
        payment_url = f"https://sandbox.mpesa.co.mz/pay/{provider_reference}"
        public_key = None
    elif country == 'CV':
        # SIBS (mock)
        provider_reference = str(uuid.uuid4())
        payment_url = f"https://sandbox.pagamentos.sibs.cv/pay/{provider_reference}"
        public_key = None
    else:
        return Response({"detail": "Country/payment method not supported"}, status=400)

    payment = Payment.objects.create(
        email=email,
        amount=amount,
        country=country,
        currency=currency,
        payment_url=payment_url,
        provider_reference=provider_reference,
        meta=meta,
    )

    return Response({
        "payment_id": payment.id,
        "payment_url": payment_url,
        "provider_reference": provider_reference,
        "country": country,
        "currency": currency,
        "public_key": public_key if country == "ZA" else None,
        "status": "pending",
    })

@api_view(['GET'])
def get_payment(request, pk):
    """
    GET payment by ID
    """
    try:
        payment = Payment.objects.get(pk=pk)
    except Payment.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    return Response(PaymentSerializer(payment).data)
