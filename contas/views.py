from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from django.template.loader import render_to_string
from rest_framework.decorators import api_view, permission_classes
from www_kudya_shop import settings

User = get_user_model()
# Reset Password Viewfrom django.template.loader import render_to_string


@permission_classes([AllowAny])
class PasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/ResetPassword?uid={uid}&token={token}"
            subject = "Solicitação de Redefinição de Senha"
            message = render_to_string(
                "password_reset_email.html",
                {
                    "username": user.username,
                    "reset_url": reset_url,
                },
            )
            send_mail(
                subject,
                "",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=message,
            )
            return Response(
                {"detail": "E-mail de redefinição de senha enviado."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Usuário com este e-mail não existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )


@permission_classes([AllowAny])
class PasswordResetConfirmView(APIView):
    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("newPassword")
        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response(
                    {"detail": "Senha foi redefinida."}, status=status.HTTP_200_OK
                )
            return Response(
                {"error": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST
            )
        except (User.DoesNotExist, ValueError):
            return Response(
                {"error": "Usuário inválido."}, status=status.HTTP_400_BAD_REQUEST
            )


# Activate Account View


@permission_classes([AllowAny])
class ActivateAccountView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            token_generator = PasswordResetTokenGenerator()

            if not token_generator.check_token(user, token):
                return Response(
                    {"message": "Token inválido ou expirado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.is_active = True
            user.save()
            return Response({"message": "Conta ativada com sucesso."})
        except User.DoesNotExist:
            return Response(
                {"message": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Erro ao ativar a conta."},
                status=status.HTTP_400_BAD_REQUEST,
            )


@permission_classes([AllowAny])
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


@permission_classes([AllowAny])
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "user_id": user.pk,
                    "username": user.username,
                    "message": "Login com sucesso",
                    "is_customer": user.is_customer,
                    "is_driver": user.is_driver,
                }
            )

        username = request.data.get("username")
        password = request.data.get("password")

        if not User.objects.filter(username=username).exists():
            return Response(
                {"message": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        user = User.objects.filter(username=username).first()
        if not user.check_password(password):
            return Response(
                {"message": "Senha incorreta."}, status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(
            {"message": "Erro desconhecido."}, status=status.HTTP_400_BAD_REQUEST
        )
