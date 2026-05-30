from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from contas.auth_helpers import user_from_access_token


User = get_user_model()


class AuthApiTests(APITestCase):
    def test_register_login_refresh_and_me_use_jwt(self):
        register = self.client.post(
            '/api/auth/register/',
            {
                'email': 'customer@example.com',
                'password': 'StrongPass123!',
                'first_name': 'Ada',
                'last_name': 'Lovelace',
                'preferred_language': 'fr',
            },
            format='json',
        )
        self.assertEqual(register.status_code, 201)
        self.assertIn('access', register.data)
        self.assertIn('refresh', register.data)
        self.assertEqual(register.data['token'], register.data['access'])
        self.assertEqual(register.data['auth_scheme'], 'Bearer')
        self.assertEqual(register.data['user']['preferred_language'], 'fr')

        login = self.client.post(
            '/api/auth/login/',
            {'username': 'customer@example.com', 'password': 'StrongPass123!'},
            format='json',
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn('access', login.data)
        self.assertIn('refresh', login.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['email'], 'customer@example.com')

        self.client.credentials()
        refresh = self.client.post(
            '/api/auth/refresh/',
            {'refresh': login.data['refresh']},
            format='json',
        )
        self.assertEqual(refresh.status_code, 200)
        self.assertIn('access', refresh.data)
        self.assertEqual(refresh.data['token'], refresh.data['access'])

    def test_user_from_access_token_accepts_jwt_and_legacy_token(self):
        user = User.objects.create_user(
            username='driver@example.com',
            email='driver@example.com',
            password='pass12345',
        )
        legacy = Token.objects.get(user=user)
        jwt_access = str(RefreshToken.for_user(user).access_token)

        self.assertEqual(user_from_access_token(legacy.key).pk, user.pk)
        self.assertEqual(user_from_access_token(jwt_access).pk, user.pk)

    def test_login_returns_api_token_alias(self):
        User.objects.create_user(
            username='shop@example.com',
            email='shop@example.com',
            password='pass12345',
        )
        login = self.client.post(
            '/api/auth/login/',
            {'username': 'shop@example.com', 'password': 'pass12345'},
            format='json',
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn('api_token', login.data)
        self.assertTrue(login.data['api_token'])
