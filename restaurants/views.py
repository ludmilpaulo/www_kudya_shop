from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import IntegrityError



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

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def fornecedor_sign_up(request, format=None):
    if request.method == "POST":
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not password:
            return Response({"message": "Nome de usuário e senha são necessários."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"message": "O nome de usuário já existe."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the User object
        new_user = User.objects.create_user(username=username, password=password, email=email)

        # Handle uploaded files
        logo = request.FILES.get('logo', None)
        licenca = request.FILES.get('restaurant_license', None)
        if logo:
            request.data['logo'] = logo
        if licenca:
            request.data['restaurant_license'] = licenca

        # Pass the request object to the serializer
        serializer = RestaurantSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            # Create the Restaurant object with the user field set
            serializer.validated_data['user'] = new_user
            restaurant = serializer.save()

            # Ensure that the logo field is set in the restaurant object
            if logo:
                restaurant.logo = logo
                restaurant.save()

            # Serialize the Restaurant object into a dictionary
            restaurant_data = RestaurantSerializer(restaurant, context={'request': request}).data

            # Authenticate the user after saving the data
            user = authenticate(username=username, password=password)
            if user is not None:
                return Response({
                    "token": Token.objects.get(user=user).key,
                    'user_id': user.pk,
                    "message": "Conta criada com sucesso",
                    "fornecedor_id": restaurant_data,  # Include the serialized restaurant data
                    'username': user.username,
                    "status": "201"
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Falha na autenticação."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



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



@api_view(['POST'])
def restaurant_order(request, format=None):
     # Print the user to verify if it's retrieved correctly
    data = request.data
    user = get_object_or_404(User, id=data['user_id'])
    print(data)

    try:
        order = Order.objects.get(id=data["id"],
                                restaurant=user.restaurant)

        if order.status == Order.COOKING:
            order.status = Order.READY
            order.save()

        orders = Order.objects.filter(
        restaurant=user.restaurant).order_by("-id")

        return Response({'message': 'Order status updated to READY'}, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


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
