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
#from django.contrib.auth.models import User
from rest_framework.parsers import *


from order.models import Order
from order.serializers import OrderSerializer
from django.contrib.auth import get_user_model

from restaurants.models import Meal, MealCategory, OpeningHour, Restaurant, RestaurantCategory
from restaurants.serializers import MealCategorySerializer, MealSerializer, OpeningHourSerializer, RestaurantCategorySerializer, RestaurantSerializer
User = get_user_model()



AccessToken = Token

def get_fornecedor(request):
    usuario_id = request.GET.get('user_id')

    # Check if the usuario_id parameter is provided
    if usuario_id:
        fornecedores = Restaurant.objects.filter(user=usuario_id)
    else:
        fornecedores = Restaurant.objects.all()

    serialized_data = RestaurantSerializer(
        fornecedores,
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"fornecedor": serialized_data})





class ProdutoListView(ListAPIView):
    serializer_class = MealSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id', None)  # Get user_id from the request parameters

        # Get the user object from the user_id
        user = get_object_or_404(User, id=user_id)

        return Meal.objects.filter(restaurant=user.restaurant).order_by("-id")
    
def restaurant_get_meals(request):
    data = request.data
      # Retrieve the user associated with the access token
    access = Token.objects.get(key=data['access_token']).user

    # Retrieve the restaurant associated with the user
    restaurant = access.restaurant


    meals = MealSerializer(
        Meal.objects.filter(restaurant_id=restaurant.id),
        many=True,
        context={
            "request": request
        }).data

    return JsonResponse({"meals": meals})

class CategoriaListCreate(generics.ListCreateAPIView):
    queryset = RestaurantCategory.objects.all()
    serializer_class = RestaurantCategorySerializer









@api_view(["POST"])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def fornecedor_add_product(request, format=None):
    data = request.data

    try:
        # Retrieve the user associated with the access token
        access = Token.objects.get(key=data['access_token']).user

        # Retrieve the restaurant associated with the user
        restaurant = access.restaurant

        # Retrieve or create the category based on the slug
        category_slug = data['category']
        try:
            category = MealCategory.objects.get(slug=category_slug)
        except MealCategory.DoesNotExist:
            category = MealCategory.objects.create(slug=category_slug, name=category_slug)

        # Convert price to float
        price = float(data['price'])

        # Create a new meal for the restaurant
        meal = Meal(
            restaurant=restaurant,
            category=category,
            name=data['name'],
            short_description=data['short_description'],
            price=price,
        )

        # Handle image file
        if 'image' in request.FILES:
            meal.image = request.FILES['image']

        try:
            # Try to save the meal
            meal.save()
        except IntegrityError:
            # If there is a unique constraint violation (e.g., duplicate name), you can handle it here
            return Response({'error': 'Meal with the same name already exists'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "Os Seus Dados enviados com sucesso"}, status=status.HTTP_201_CREATED)

    except Token.DoesNotExist:
        return Response({'error': 'Invalid access token'}, status=status.HTTP_401_UNAUTHORIZED)

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)





@api_view(['DELETE'])
#@permission_classes([IsAuthenticated])
def delete_product(request, pk):
    try:
        # Authenticate the user using the user_id from the request
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id not provided'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(pk=user_id)

        # Check if the user has permission to delete the product
        product = Meal.objects.get(pk=pk)
        if not hasattr(user, 'restaurant') or user.restaurant != product.restaurant:
            return Response({'error': 'User does not have permission to delete this product'}, status=status.HTTP_403_FORBIDDEN)

        # User is authenticated and has permission, delete the product
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Meal.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    


@api_view(['PUT'])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def update_product(request, pk):
    try:
        # Authenticate the user using the user_id from the request
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id not provided'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(pk=user_id)

        # Check if the user has permission to update the product
        product = Meal.objects.get(pk=pk)
        if not hasattr(user, 'restaurant') or user.restaurant != product.restaurant:
            return Response({'error': 'User does not have permission to update this product'}, status=status.HTTP_403_FORBIDDEN)

        # Update the product
        data = request.data
        category_slug = data.get('category')
        try:
            category = MealCategory.objects.get(slug=category_slug)
        except MealCategory.DoesNotExist:
            category = MealCategory.objects.create(slug=category_slug, name=category_slug)
        
        product.category = category
        product.name = data.get('name', product.name)
        product.short_description = data.get('short_description', product.short_description)
        product.price = float(data.get('price', product.price))
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()

        serializer = MealSerializer(product, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Meal.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



# views.py
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404

import json
import time

def sse(request):
    user_id = request.GET.get('user_id')
    user = get_object_or_404(User, id=user_id)

    def event_stream():
        while True:
            orders = Order.objects.filter(restaurant=user.restaurant).order_by("-id")
            serializer = OrderSerializer(orders, many=True)
            data = JSONRenderer().render(serializer.data)
            yield f"data: {data.decode('utf-8')}\n\n"
            time.sleep(5)  # Adjust the interval as needed

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')



class OrderListView(ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id', None)  # Get user_id from the request parameters

        # Get the user object from the user_id
        user = get_object_or_404(User, id=user_id)

        return Order.objects.filter(restaurant=user.restaurant).order_by("-id")

class RestaurantCategoryList(generics.ListAPIView):
    queryset = RestaurantCategory.objects.all()
    serializer_class = RestaurantCategorySerializer

class MealCategoryList(generics.ListAPIView):
    queryset = MealCategory.objects.all()
    serializer_class = MealCategorySerializer
    
    


@api_view(['GET', 'PUT'])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def restaurant_detail(request, user_id):
    try:
        user = get_object_or_404(User, pk=user_id)
        restaurant = get_object_or_404(Restaurant, user=user)
        if request.method == 'GET':
            serializer = RestaurantSerializer(restaurant, context={'request': request})
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = RestaurantSerializer(restaurant, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)
    
    
    
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import OpeningHour
from .serializers import OpeningHourSerializer

@api_view(['GET', 'POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def opening_hour_list(request, restaurant_pk):
    if request.method == 'GET':
        opening_hours = OpeningHour.objects.filter(restaurant_id=restaurant_pk)
        serializer = OpeningHourSerializer(opening_hours, many=True, context={'request': request})
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data
        print("Received data:", data)
        data['restaurant'] = restaurant_pk
        serializer = OpeningHourSerializer(data=data, context={'request': request})
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


@api_view(['PUT'])
def restaurant_order(request, format=None):
    print("Received PUT request")
    data = request.data
    user = get_object_or_404(User, id=data['user_id'])
    try:
        order = Order.objects.get(id=data["id"], restaurant=user.restaurant)
        print(f"Order {order.id} found")

        if order.status == Order.COOKING:
            order.status = Order.READY
            order.save()

        orders = Order.objects.filter(restaurant=user.restaurant).order_by("-id")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({'error': 'Pedido não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    
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
        return Response({'error': 'user_id and location are required'}, status=400)

    try:
        logger.info(f"Request data: {data}")
        restaurant = get_object_or_404(Restaurant, user__id=user_id)
        logger.info(f"Found restaurant: {restaurant}")
        restaurant.location = location
        restaurant.save()
        logger.info(f"Location updated successfully for user ID: {user_id}")
        return Response({'message': 'Location updated successfully'}, status=200)
    except Exception as e:
        logger.error(f"Error updating location for user ID: {user_id} - {str(e)}")
        return Response({'error': str(e)}, status=500)


