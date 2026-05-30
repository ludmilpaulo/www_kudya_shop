from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.authtoken.models import Token

User = get_user_model()


def _user_payload(user):
    return {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': getattr(user, 'role', 'customer'),
        'phone': getattr(user, 'phone', ''),
        'preferred_language': getattr(user, 'preferred_language', 'en'),
        'country': user.country_id,
        'city': user.city_id,
        'is_verified': getattr(user, 'is_verified', False),
    }


def _auth_payload(user, refresh):
    access = str(refresh.access_token)
    # Legacy partner/driver endpoints read access_token from JSON body.
    legacy_token, _ = Token.objects.get_or_create(user=user)
    return {
        'access': access,
        'refresh': str(refresh),
        'token': access,
        'api_token': legacy_token.key,
        'auth_scheme': 'Bearer',
        'user': _user_payload(user),
        'user_id': user.id,
        'username': user.username,
        'is_customer': getattr(user, 'is_customer', False),
        'is_driver': getattr(user, 'is_driver', False),
        'message': 'Login com sucesso',
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get('email', request.data.get('username', ''))
    password = request.data.get('password', '')
    if not email or not password:
        return Response({'detail': 'Email and password required.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=email).exists():
        return Response({'detail': 'User already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=request.data.get('first_name', ''),
        last_name=request.data.get('last_name', ''),
    )
    user.is_customer = True
    user.role = 'customer'
    if hasattr(user, 'preferred_language'):
        user.preferred_language = request.data.get('preferred_language', 'en')
    user.save()
    refresh = RefreshToken.for_user(user)
    return Response(_auth_payload(user, refresh), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('email', request.data.get('username', ''))
    password = request.data.get('password', '')
    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'detail': 'Invalid credentials.', 'message': 'Falha ao entrar. Verifique usuário e senha.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    refresh = RefreshToken.for_user(user)
    return Response(_auth_payload(user, refresh))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get('refresh')
    if refresh_token:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Logged out.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    serializer = TokenRefreshSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
    except TokenError:
        return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)
    data = serializer.validated_data
    access = data.get('access', '')
    return Response({
        **data,
        'token': access,
        'auth_scheme': 'Bearer',
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == 'PATCH':
        user = request.user
        for field in ('first_name', 'last_name', 'phone', 'preferred_language'):
            if field in request.data and hasattr(user, field):
                setattr(user, field, request.data[field])
        if 'country' in request.data:
            user.country_id = request.data['country']
        if 'city' in request.data:
            user.city_id = request.data['city']
        user.save()
    return Response(_user_payload(request.user))
