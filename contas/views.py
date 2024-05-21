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
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated

from www_kudya_shop import settings
User = get_user_model()
# Reset Password View
class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'message': 'Email é necessário.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            send_mail(
                'Redefinição de Senha',
                f'Clique no link para redefinir sua senha: {reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return Response({'message': 'Email de redefinição de senha enviado com sucesso.'})
        except User.DoesNotExist:
            return Response({'message': 'Email não encontrado. Por favor, cadastre-se.'}, status=status.HTTP_404_NOT_FOUND)

# Password Reset Confirm View
class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            token_generator = PasswordResetTokenGenerator()

            if not token_generator.check_token(user, token):
                return Response({'message': 'Token inválido ou expirado.'}, status=status.HTTP_400_BAD_REQUEST)

            new_password = request.data.get('password')
            if not new_password:
                return Response({'message': 'Nova senha é necessária.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.is_active = False  # Deactivate the user account
            user.save()

            # Generate activation token
            activation_token = token_generator.make_token(user)
            activation_uid = urlsafe_base64_encode(force_bytes(user.pk))

            activation_url = request.build_absolute_uri(
                reverse('activate_account', kwargs={'uidb64': activation_uid, 'token': activation_token})
            )

            send_mail(
                'Ativar Conta',
                f'Sua senha foi redefinida com sucesso. Clique no link para ativar sua conta: {activation_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({'message': 'Senha redefinida com sucesso. Verifique seu email para ativar sua conta.'})
        except User.DoesNotExist:
            return Response({'message': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': 'Erro ao redefinir a senha.'}, status=status.HTTP_400_BAD_REQUEST)

# Activate Account View
class ActivateAccountView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            token_generator = PasswordResetTokenGenerator()

            if not token_generator.check_token(user, token):
                return Response({'message': 'Token inválido ou expirado.'}, status=status.HTTP_400_BAD_REQUEST)

            user.is_active = True
            user.save()
            return Response({'message': 'Conta ativada com sucesso.'})
        except User.DoesNotExist:
            return Response({'message': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': 'Erro ao ativar a conta.'}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)




class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'message': "Login com sucesso",
                'is_customer': user.is_customer
            })

        username = request.data.get('username')
        password = request.data.get('password')

        if not User.objects.filter(username=username).exists():
            return Response({'message': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        user = User.objects.filter(username=username).first()
        if not user.check_password(password):
            return Response({'message': 'Senha incorreta.'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({'message': 'Erro desconhecido.'}, status=status.HTTP_400_BAD_REQUEST)






