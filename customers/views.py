from django.http import JsonResponse
from rest_framework.response import Response


from contas.serializers import CustomerSignupSerializer, UserSerializer
from customers.models import Customer
from customers.serializers import CustomerSerializer
from order.models import Order, OrderDetails
from order.serializers import OrderSerializer
from rest_framework.decorators import *
from rest_framework.authtoken.models import Token


from rest_framework import status, generics, permissions, viewsets
from rest_framework.parsers import *


from django.contrib.auth import get_user_model

from stores.models import Product, Store
from stores.serializers import ProductSerializer, StoreSerializer

User = get_user_model()


AccessToken = Token


####################################################
# CUSTOMERS
####################################################


@api_view(["POST"])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def customer_update_profile(request, format=None):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    # Try to get or create the Customer object
    customer, created = Customer.objects.get_or_create(user=access)

    # Handle avatar if uploaded
    if "avatar" in request.FILES:
        customer.avatar = request.FILES["avatar"]

    customer.phone = data.get("phone", customer.phone)
    customer.address = data.get("address", customer.address)
    customer.location = data.get("location", customer.location)
    customer.save()

    # Update User's first/last name if given
    access.first_name = data.get("first_name", access.first_name)
    access.last_name = data.get("last_name", access.last_name)
    access.save()

    return JsonResponse({"status": "Os Seus Dados enviados com sucesso"})


def customer_get_stores(request):
    stores = StoreSerializer(
        Store.objects.all().order_by("-id"),
        many=True,
        context={"request": request},
    ).data

    return JsonResponse({"stores": stores})


def customer_get_products(request, store_id):
    products = ProductSerializer(
        Product.objects.filter(store_id=store_id).order_by("-id"),
        many=True,
        context={"request": request},
    ).data

    return JsonResponse({"products": products})


#######################################################################################3


@api_view(["GET"])
def customer_get_detais(request):
    user_id = request.query_params.get("user_id")
    print(f"Received user_id: {user_id}")
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)

    try:
        customer = Customer.objects.get(user_id=user_id)
        customer_details = CustomerSerializer(customer).data
        return JsonResponse({"customer_details": customer_details})
    except Customer.DoesNotExist:
        return JsonResponse({"error": "Customer not found"}, status=404)


##################################################################
# @csrf_exempt
@api_view(["POST"])
def customer_add_order(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    # Get profile

    customer = Customer.objects.get(user=access)

    if Order.objects.filter(customer=customer).exclude(status=Order.DELIVERED):
        return JsonResponse(
            {
                "error": "failed",
                "status": "Seu último pedido deve ser entregue para Pedir Outro.",
            }
        )

    # Check Address
    if not data["address"]:
        return JsonResponse({"status": "failed", "error": "Address is required."})

    # Get Order Details

    order_details = data["order_details"]

    order_total = 0
    for product in order_details:
        order_total += product.objects.get(id=product["product_id"]).price * product["quantity"]

    if len(order_details) > 0:

        # Step 2 - Create an Order
        order = Order.objects.create(
            customer=customer,
            store_id=data["store_id"],
            total=order_total,
            status=Order.COOKING,
            address=data["address"],
        )

        # Step 3 - Create Order details
        for product in order_details:
            OrderDetails.objects.create(
                order=order,
                product_id=product["product_id"],
                quantity=product["quantity"],
                sub_total=product.objects.get(id=product["product_id"]).price * product["quantity"],
            )
        # serializer = OrderSerializer(order, many=False)
        return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "failed", "error": "Failed connect to Stripe."})


##############################################################


@api_view(["POST"])
def customer_get_latest_order(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    # Get profile
    customer = Customer.objects.get(user=access)
    # Get all orders that are not delivered
    orders = Order.objects.filter(customer=customer).exclude(status=Order.DELIVERED)
    orders_data = OrderSerializer(orders, many=True).data

    return JsonResponse({"orders": orders_data})


@api_view(["POST"])
def customer_driver_location(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    # Get profile
    customer = Customer.objects.get(user=access)

    # Get all orders that are not delivered
    orders = Order.objects.filter(customer=customer).exclude(status=Order.DELIVERED)
    
    # Collect locations for orders with drivers
    order_locations = []
    for order in orders:
        if order.driver:
            order_locations.append({
                'order_id': order.id,
                'driver_location': order.driver.location,
                'secret_pin': order.secret_pin
            })
        else:
            order_locations.append({
                'order_id': order.id,
                'driver_location': None,
                'store': order.store.name,
                'secret_pin': order.secret_pin
            })

    return JsonResponse({"order_locations": order_locations})



# GET params: access_token
@api_view(["POST"])
def customer_get_order_history(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    # Get profile

    customer = Customer.objects.get(user=access)
    order_history = OrderSerializer(
        Order.objects.filter(customer=customer, status=Order.DELIVERED).order_by(
            "picked_at"
        ),
        many=True,
        context={"request": request},
    ).data

    return JsonResponse({"order_history": order_history})


class CustomerSignupView(generics.GenericAPIView):
    serializer_class = CustomerSignupSerializer

    def post(self, request, *args, **kwargs):
        # Check if the username already exists
        if User.objects.filter(username=request.data.get("username")).exists():
            return Response(
                {"message": "Este nome de usuário já existe.", "status": "400"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the email already exists
        if User.objects.filter(email=request.data.get("email")).exists():
            return Response(
                {"message": "Este email já está em uso.", "status": "400"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "token": Token.objects.get(user=user).key,
                "user_id": user.pk,
                "message": "Conta criada com sucesso",
                "username": user.username,
                "status": "201",
                "is_customer": user.is_customer,
            },
            status=status.HTTP_201_CREATED,
        )


from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    customer, created = Customer.objects.get_or_create(user=user)
    serializer = CustomerSerializer(customer, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success"}, status=status.HTTP_200_OK)
    return Response(
        {"status": "error", "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )
