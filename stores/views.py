from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import *
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView


from django.contrib.auth import authenticate

# from django.contrib.auth.models import User
from rest_framework.parsers import *


from order.models import Order
from order.serializers import OrderSerializer
from django.contrib.auth import get_user_model

from stores.models import (
    Product,
    ProductCategory,
    OpeningHour,
    Store,
    StoreCategory,
)
from stores.serializers import (
    ProductCategorySerializer,
    ProductSerializer,
    OpeningHourSerializer,
    StoreCategorySerializer,
    StoreSerializer,
)

User = get_user_model()


AccessToken = Token


def get_fornecedor(request):
    usuario_id = request.GET.get("user_id")

    # Check if the usuario_id parameter is provided
    if usuario_id:
        fornecedores = Store.objects.filter(user=usuario_id)
    else:
        fornecedores = Store.objects.all()

    serialized_data = StoreSerializer(
        fornecedores, many=True, context={"request": request}
    ).data

    return JsonResponse({"fornecedor": serialized_data})


class ProdutoListView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get(
            "user_id", None
        )  # Get user_id from the request parameters

        # Get the user object from the user_id
        user = get_object_or_404(User, id=user_id)

        return Product.objects.filter(store=user.store).order_by("-id")


def store_get_products(request):
    data = request.data
    # Retrieve the user associated with the access token
    access = Token.objects.get(key=data["access_token"]).user

    # Retrieve the store associated with the user
    store = access.store

    products = ProductSerializer(
        Product.objects.filter(store_id=store.id),
        many=True,
        context={"request": request},
    ).data

    return JsonResponse({"products": products})


class CategoriaListCreate(generics.ListCreateAPIView):
    queryset = StoreCategory.objects.all()
    serializer_class = StoreCategorySerializer


from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import (
    JSONParser,
    MultiPartParser,
    FormParser,
    FileUploadParser,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from .models import Product, ProductCategory


@api_view(["POST"])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def fornecedor_add_product(request, format=None):
    data = request.data
    print("Request data:", data)

    try:
        # Retrieve the user associated with the access token
        access_token = data.get("access_token")
        if not access_token:
            return Response(
                {"error": "Access token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access = Token.objects.get(key=access_token).user
        print("User associated with token:", access)

        # Retrieve the store associated with the user
        try:
            store = access.store
        except store.DoesNotExist:
            return Response(
                {"error": "store not found for the user"},
                status=status.HTTP_404_NOT_FOUND,
            )
        print("store associated with user:", store)

        # Retrieve or create the category based on the slug
        category_slug = data.get("category")
        if not category_slug:
            return Response(
                {"error": "Category slug is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            category = ProductCategory.objects.get(slug=category_slug)
        except ProductCategory.DoesNotExist:
            category = ProductCategory.objects.create(
                slug=category_slug, name=category_slug
            )
        print("product category:", category)

        # Convert price to float
        price = data.get("price")
        if not price:
            return Response(
                {"error": "Price is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            price = float(price)
        except ValueError:
            return Response(
                {"error": "Invalid price format"}, status=status.HTTP_400_BAD_REQUEST
            )
        print("Price:", price)

        # Retrieve quantity if provided, otherwise use default
        quantity = data.get("quantity", 1)
        try:
            quantity = int(quantity)
        except ValueError:
            return Response(
                {"error": "Invalid quantity format"}, status=status.HTTP_400_BAD_REQUEST
            )
        print("Quantity:", quantity)

        # Create a new product for the store
        product = Product(
            store=store,
            category=category,
            name=data.get("name"),
            short_description=data.get("short_description"),
            price=price,
            quantity=quantity,
        )
        print("product object created:", product)

        # Handle image file
        if "image" in request.FILES:
            product.image = request.FILES["image"]
            print("Image file received")

        try:
            # Try to save the product
            product.save()
            print("product saved successfully")
        except IntegrityError as e:
            print("IntegrityError:", str(e))
            return Response(
                {"error": "product with the same name already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"status": "Os Seus Dados enviados com sucesso"},
            status=status.HTTP_201_CREATED,
        )

    except Token.DoesNotExist as e:
        print("Token.DoesNotExist:", str(e))
        return Response(
            {"error": "Invalid access token"}, status=status.HTTP_401_UNAUTHORIZED
        )

    except store.DoesNotExist as e:
        print("store.DoesNotExist:", str(e))
        return Response(
            {"error": "store not found for the user"},
            status=status.HTTP_404_NOT_FOUND,
        )

    except ValueError as e:
        print("ValueError:", str(e))
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print("Unexpected error:", str(e))
        return Response(
            {"error": "Unexpected error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

###########################################

import logging

logger = logging.getLogger(__name__)

@api_view(["DELETE"])
def delete_product(request, pk):
    try:
        user_id = request.data.get("user_id")
        if not user_id:
            logger.error("user_id not provided")
            return Response(
                {"error": "user_id not provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(pk=user_id)
        product = Product.objects.get(pk=pk)
        
        if not hasattr(user, "store") or user.store != product.store:
            logger.error("User does not have permission to delete this product")
            return Response(
                {"error": "User does not have permission to delete this product"},
                status=status.HTTP_403_FORBIDDEN,
            )

        product.delete()
        logger.info(f"Product {pk} deleted successfully")
        return Response(status=status.HTTP_204_NO_CONTENT)

    except User.DoesNotExist:
        logger.error("User not found")
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except product.DoesNotExist:
        logger.error("Product not found")
        return Response(
            {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    
    

@api_view(["PUT"])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def update_product(request, pk):
    try:
        # Authenticate the user using the user_id from the request
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"error": "user_id not provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(pk=user_id)

        # Check if the user has permission to update the product
        product = Product.objects.get(pk=pk)
        if not hasattr(user, "store") or user.store != product.store:
            return Response(
                {"error": "User does not have permission to update this product"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update the product
        data = request.data
        category_slug = data.get("category")
        try:
            category = ProductCategory.objects.get(slug=category_slug)
        except ProductCategory.DoesNotExist:
            category = ProductCategory.objects.create(
                slug=category_slug, name=category_slug
            )

        product.category = category
        product.name = data.get("name", product.name)
        product.short_description = data.get(
            "short_description", product.short_description
        )
        product.price = float(data.get("price", product.price))

        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()

        serializer = ProductSerializer(product, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except product.DoesNotExist:
        return Response(
            {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# views.py
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404

import json
import time


def sse(request):
    user_id = request.GET.get("user_id")
    user = get_object_or_404(User, id=user_id)

    def event_stream():
        while True:
            orders = Order.objects.filter(store=user.store).order_by("-id")
            serializer = OrderSerializer(orders, many=True)
            data = JSONRenderer().render(serializer.data)
            yield f"data: {data.decode('utf-8')}\n\n"
            time.sleep(5)  # Adjust the interval as needed

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


class OrderListView(ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get(
            "user_id", None
        )  # Get user_id from the request parameters

        # Get the user object from the user_id
        user = get_object_or_404(User, id=user_id)

        return Order.objects.filter(store=user.store).order_by("-id")


class StoreCategoryList(generics.ListAPIView):
    queryset = StoreCategory.objects.all()
    serializer_class = StoreCategorySerializer


class ProductCategoryList(generics.ListAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer


@api_view(["GET", "PUT"])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def store_detail(request, user_id):
    try:
        user = get_object_or_404(User, pk=user_id)
        store = get_object_or_404(store, user=user)
        if request.method == "GET":
            serializer = StoreSerializer(store, context={"request": request})
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = StoreSerializer(
                store,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except store.DoesNotExist:
        return Response(
            {"error": "store not found"}, status=status.HTTP_404_NOT_FOUND
        )


from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import OpeningHour
from .serializers import OpeningHourSerializer


@api_view(["GET", "POST"])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def opening_hour_list(request, store_pk):
    if request.method == "GET":
        opening_hours = OpeningHour.objects.filter(store_id=store_pk)
        serializer = OpeningHourSerializer(
            opening_hours, many=True, context={"request": request}
        )
        return Response(serializer.data)
    elif request.method == "POST":
        data = request.data
        print("Received data:", data)
        data["store"] = store_pk
        serializer = OpeningHourSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(["PUT"])
def store_order(request, format=None):
    print("Received PUT request")
    data = request.data
    user = get_object_or_404(User, id=data["user_id"])
    try:
        order = Order.objects.get(id=data["id"], store=user.store)
        print(f"Order {order.id} found")

        if order.status == Order.COOKING:
            order.status = Order.READY
            order.save()

        orders = Order.objects.filter(store=user.store).order_by("-id")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response(
            {"error": "Pedido não encontrado"}, status=status.HTTP_404_NOT_FOUND
        )


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
def update_location(request):
    data = request.data
    user_id = data.get("user_id")
    location = data.get("location")

    if not user_id or not location:
        return Response({"error": "user_id and location are required"}, status=400)

    try:
        logger.info(f"Request data: {data}")
        store = get_object_or_404(store, user__id=user_id)
        logger.info(f"Found store: {store}")
        store.location = location
        store.save()
        logger.info(f"Location updated successfully for user ID: {user_id}")
        return Response({"message": "Location updated successfully"}, status=200)
    except Exception as e:
        logger.error(f"Error updating location for user ID: {user_id} - {str(e)}")
        return Response({"error": str(e)}, status=500)
