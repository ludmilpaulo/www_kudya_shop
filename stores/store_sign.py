from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import StoreSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def fornecedor_sign_up(request, format=None):
    if request.method == "POST":
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"message": "Nome de usuário e senha são necessários."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"message": "O nome de usuário já existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_user = User.objects.create_user(
            username=username, password=password, email=email
        )

        logo = request.FILES.get("logo")
        licenca = request.FILES.get("store_license")

        data = request.data.copy()
        if logo:
            data["logo"] = logo
        if licenca:
            data["store_license"] = licenca

        serializer = StoreSerializer(data=data, context={"request": request})

        if serializer.is_valid():
            serializer.validated_data["user"] = new_user
            store = serializer.save()

            if logo:
                store.logo = logo
            if licenca:
                store.store_license = licenca
            store.save()

            store_data = StoreSerializer(
                store, context={"request": request}
            ).data

            user = authenticate(username=username, password=password)
            if user is not None:
                token, _ = Token.objects.get_or_create(user=user)
                return Response(
                    {
                        "token": token.key,
                        "user_id": user.pk,
                        "message": "Conta criada com sucesso",
                        "fornecedor_id": store_data,
                        "username": user.username,
                        "status": "201",
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"error": "Falha na autenticação."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
