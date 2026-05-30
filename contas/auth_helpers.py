"""Resolve authenticated user from legacy DRF tokens or JWT access strings."""
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class AccessTokenError(Exception):
    """Invalid or missing access token."""


def user_from_access_token(token: str) -> User:
    """
    Accept either:
    - DRF authtoken key (legacy mobile / partner body param)
    - SimpleJWT access token (api/auth/login, api/auth/social)
    """
    if not token or not str(token).strip():
        raise AccessTokenError('access_token required')

    key = str(token).strip()

    try:
        return Token.objects.select_related('user').get(key=key).user
    except Token.DoesNotExist:
        pass

    try:
        validated = AccessToken(key)
        user_id = validated.get('user_id')
        if not user_id:
            raise AccessTokenError('Invalid access token.')
        return User.objects.get(pk=user_id)
    except (TokenError, InvalidToken, User.DoesNotExist) as exc:
        raise AccessTokenError('Invalid or expired access token.') from exc


def user_from_request(request, *, body_key: str = 'access_token', query_key: str = 'access_token') -> User:
    """Prefer authenticated JWT user; else resolve token from body or query."""
    if getattr(request, 'user', None) and request.user.is_authenticated:
        return request.user

    token = None
    if hasattr(request, 'data') and request.data:
        token = request.data.get(body_key)
    if not token and hasattr(request, 'GET'):
        token = request.GET.get(query_key)
    if not token:
        raise AccessTokenError('access_token required')
    return user_from_access_token(token)
