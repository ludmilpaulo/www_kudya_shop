from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate

from rest_framework.authtoken.models import Token
from .serializers import RestaurantSerializer

from django.contrib.auth import get_user_model
User = get_user_model()

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def fornecedor_sign_up(request, format=None):
    if request.method == "POST":
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        print(f"Received data: username={username}, email={email}, password={password}")

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
        print(f"Serializer initial data: {serializer.initial_data}")

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

        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
