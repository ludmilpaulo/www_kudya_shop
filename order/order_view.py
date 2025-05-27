from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from curtomers.models import Customer
from order.email_utils import send_order_email
from order.models import Coupon, Order, OrderDetails
from order.utils import generate_invoice
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.core.files.base import ContentFile
from decimal import Decimal
import urllib.parse
import logging

from stores.models import product

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(["POST"])
def customer_add_order(request):
    data = request.data
    print(data)
    try:
        access = Token.objects.get(key=data["access_token"]).user
    except Token.DoesNotExist:
        return Response({"status": "failed", "error": "Invalid access token."})

    logger.info(f"Received order data: {data}")

    # Get profile
    try:
        customer = Customer.objects.get(user=access)
    except Customer.DoesNotExist:
        return Response({"status": "failed", "error": "Customer profile not found."})

    # Check for existing orders to the same store that are not delivered
    existing_orders = Order.objects.filter(
        customer=customer, store_id=data["store_id"]
    ).exclude(status=Order.DELIVERED)
    if existing_orders.exists():
        return Response(
            {
                "status": "failed",
                "error": "Seu último pedido deve ser entregue para Pedir Outro.",
            }
        )

    # Check Address
    address = data.get("address")
    use_current_location = data.get("use_current_location", False)
    if not address and not use_current_location:
        return Response({"status": "failed", "error": "Address or current location is required."})

    # Get Order Details
    order_details = data.get("order_details", [])
    if not order_details:
        return Response({"status": "failed", "error": "Order details are required."})

    # Check for a coupon code
    coupon_code = data.get("coupon_code")
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
            if coupon.order_count < 10:
                return Response({"status": "failed", "error": "Cupom inválido. Você deve fazer pelo menos 10 pedidos para usar o cupom."})
        except Coupon.DoesNotExist:
            return Response({"status": "failed", "error": "Código de cupom inválido ou expirado."})


    order_total = 0
    original_total = 0
    for product in order_details:
        try:
            product_obj = product.objects.get(id=product["product_id"])
            product_price_with_markup = product_obj.price_with_markup
            order_total += product_price_with_markup * product["quantity"]
            original_total += product_obj.price * product["quantity"]
        except product.DoesNotExist:
            return Response(
                {
                    "status": "failed",
                    "error": f"product with ID {product['product_id']} not found.",
                }
            )

    # Calculate driver commission
    driver_commission_percentage = Order.DRIVER_COMMISSION_PERCENTAGE_DEFAULT
    driver_commission = (order_total * driver_commission_percentage) / 100
    
    # Apply discount
    discount_amount = Decimal(0)
    if coupon:
        discount_amount = (order_total * Decimal(coupon.discount_percentage)) / 100

    # Convert delivery fee to Decimal
    delivery_fee = Decimal(data["delivery_fee"])

    # Final order total
    final_total = order_total + delivery_fee - discount_amount
  
    # Step 2 - Create an Order
    try:
       order = Order.objects.create(
            customer=customer,
            store_id=data["store_id"],
            total=final_total,
            status=Order.PROCESSING,
            address=address if not use_current_location else "",
            location=data["location"],
            use_current_location =data["use_current_location"],
            payment_method=data["payment_method"],
            original_price=original_total,
            driver_commission=(order_total * Order.DRIVER_COMMISSION_PERCENTAGE_DEFAULT) / 100,
            delivery_fee=data["delivery_fee"],
            discount_amount=discount_amount,
            coupon=coupon,
            delivery_notes=data.get("delivery_notes", ""),
        )
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return Response({"status": "failed", "error": "Error creating order."})

    # Step 3 - Create Order details
    for product in order_details:
        try:
            product_obj = product.objects.get(id=product["product_id"])
            product_price_with_markup = product_obj.price_with_markup
            OrderDetails.objects.create(
                order=order,
                product_id=product["product_id"],
                quantity=product["quantity"],
                sub_total=product_price_with_markup * product["quantity"],
            )
        except Exception as e:
            logger.error(f"Error creating order details: {e}")
            return Response(
                {"status": "failed", "error": "Error creating order details."}
            )

    # Generate invoice
    try:
        pdf_path, pdf_content = generate_invoice(order)
        order.invoice_pdf.save(
            f"order_{order.id}.pdf", ContentFile(pdf_content), save=False
        )
        order.save()
    except Exception as e:
        logger.error(f"Error generating invoice: {e}")
        return Response({"status": "failed", "error": "Error generating invoice."})

    try:
        # Send email notifications
        send_order_email(
            to_email=customer.user.email,
            order=order,
            pdf_path=pdf_path,
            pdf_content=pdf_content,
        )
        store_email = order.store.user.email
        send_order_email(
            to_email=store_email,
            order=order,
            pdf_path=pdf_path,
            pdf_content=pdf_content,
            is_store=True,
        )
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return Response(
            {
                "status": "failed",
                "error": "Erro ao enviar email. Por favor, tente novamente.",
            }
        )


    # Generate WhatsApp URL
    phone_number = "customer_phone_number"  # Replace with the actual phone number
    message = f"Olá {customer.user.get_full_name()}, seu pedido foi recebido com sucesso. Seu PIN secreto é {order.secret_pin}."
    whatsapp_url = f"https://wa.me/{phone_number}?text={urllib.parse.quote(message)}"

    return Response(
        {
            "status": "success",
            "secret_pin": order.secret_pin,
            "whatsapp_url": whatsapp_url,
        }
    )



@api_view(["POST"])
def check_user_coupon(request):
    data = request.data
    try:
        access = Token.objects.get(key=data["access_token"]).user
    except Token.DoesNotExist:
        return Response({"status": "failed", "error": "Token de acesso inválido."})

    # Get profile
    try:
        customer = Customer.objects.get(user=access)
    except Customer.DoesNotExist:
        return Response({"status": "failed", "error": "Perfil do cliente não encontrado."})

    try:
        # Check if the coupon exists and is associated with the user
        coupon = Coupon.objects.filter(user=customer.user).first()
        if coupon and coupon.order_count >= 10:
            return Response({"status": "success", "coupon_code": coupon.code})
        else:
            return Response({"status": "failed", "error": "Nenhum cupom válido disponível"})
    except Coupon.DoesNotExist:
        return Response({"status": "failed", "error": "Nenhum cupom válido disponível"})
