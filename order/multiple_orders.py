from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from customers.models import Customer
from order.models import Order, OrderDetails
from order.utils import generate_invoice
from order.email_utils import send_order_email
from stores.models.product import Product
from decimal import Decimal
from django.core.files.base import ContentFile

@api_view(["POST"])
def customer_add_multiple_orders(request):
    data = request.data
    try:
        access = Token.objects.get(key=data["access_token"]).user
    except Token.DoesNotExist:
        return Response({"status": "failed", "error": "Invalid access token."})

    try:
        customer = Customer.objects.get(user=access)
    except Customer.DoesNotExist:
        return Response({"status": "failed", "error": "Customer profile not found."})

    created_orders = []
    order_pins = []
    whatsapp_urls = []
    errors = []

    for order_data in data.get("orders", []):
        store_id = order_data["store_id"]
        address = order_data.get("address", "")
        location = order_data.get("location", "")
        use_current_location = order_data.get("use_current_location", False)
        delivery_fee = Decimal(order_data.get("delivery_fee", "0"))
        payment_method = order_data["payment_method"]
        delivery_notes = order_data.get("delivery_notes", "")

        existing_orders = Order.objects.filter(
            customer=customer, store_id=store_id
        ).exclude(status=Order.DELIVERED)

        if existing_orders.exists():
            errors.append({
                "store_id": store_id,
                "error": "You already have an undelivered order for this store."
            })
            continue

        order_total = 0
        original_total = 0
        order_details_data = order_data["order_details"]

        try:
            for item in order_details_data:
                product = Product.objects.get(id=item["product_id"])
                order_total += product.price_with_markup * item["quantity"]
                original_total += product.price * item["quantity"]
        except Product.DoesNotExist:
            errors.append({
                "store_id": store_id,
                "error": f"Product with ID {item['product_id']} not found."
            })
            continue

        driver_commission_percentage = Order.DRIVER_COMMISSION_PERCENTAGE_DEFAULT
        driver_commission = (order_total * driver_commission_percentage) / 100
        final_total = order_total + delivery_fee

        try:
            order = Order.objects.create(
                customer=customer,
                store_id=store_id,
                total=final_total,
                status=Order.PROCESSING,
                address=address if not use_current_location else "",
                location=location,
                use_current_location=use_current_location,
                payment_method=payment_method,
                original_price=original_total,
                driver_commission=driver_commission,
                delivery_fee=delivery_fee,
                delivery_notes=delivery_notes,
            )

            for item in order_details_data:
                product = Product.objects.get(id=item["product_id"])
                OrderDetails.objects.create(
                    order=order,
                    product_id=product.id,
                    quantity=item["quantity"],
                    sub_total=product.price_with_markup * item["quantity"]
                )

            pdf_path, pdf_content = generate_invoice(order)
            order.invoice_pdf.save(f"order_{order.id}.pdf", ContentFile(pdf_content), save=True)

            send_order_email(to_email=customer.user.email, order=order, pdf_path=pdf_path, pdf_content=pdf_content)
            send_order_email(to_email=order.store.user.email, order=order, pdf_path=pdf_path, pdf_content=pdf_content, is_store=True)

            # WhatsApp integration (replace placeholder number)
            phone_number = "customer_phone_number"
            message = f"Olá {customer.user.get_full_name()}, pedido {order.id} recebido com sucesso. PIN: {order.secret_pin}."
            whatsapp_url = f"https://wa.me/{phone_number}?text={urllib.parse.quote(message)}"

            created_orders.append(order.id)
            order_pins.append({"order_id": order.id, "pin": order.secret_pin})
            whatsapp_urls.append(whatsapp_url)
        except Exception as e:
            errors.append({
                "store_id": store_id,
                "error": str(e)
            })

    if errors:
        return Response({
            "status": "partial_success",
            "created_orders": created_orders,
            "order_pins": order_pins,
            "whatsapp_urls": whatsapp_urls,
            "errors": errors
        })

    return Response({
        "status": "success",
        "created_orders": created_orders,
        "order_pins": order_pins,
        "whatsapp_urls": whatsapp_urls,
    })
