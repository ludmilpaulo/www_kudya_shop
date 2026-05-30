"""Social OAuth login — link or create users from verified provider tokens."""
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .api_views import _auth_payload
from .models import SocialAccount
from .social_auth import SocialAuthError, verify_social_token

User = get_user_model()

SUPPORTED_PROVIDERS = {'google', 'facebook', 'instagram', 'tiktok'}


def _username_for_profile(profile) -> str:
    email = (profile.get('email') or '').strip().lower()
    if email and '@' in email and not email.endswith('.local'):
        return email
    return f"{profile['provider']}_{profile['provider_user_id']}@kudya.social"


@transaction.atomic
def _get_or_create_user_from_profile(profile):
    provider = profile['provider']
    provider_user_id = profile['provider_user_id']

    social = (
        SocialAccount.objects.select_related('user')
        .filter(provider=provider, provider_user_id=provider_user_id)
        .first()
    )
    if social:
        user = social.user
        social.email = profile.get('email') or social.email
        social.extra_data = profile
        social.save(update_fields=['email', 'extra_data', 'updated_at'])
        return user, False

    email = (profile.get('email') or '').strip().lower()
    user = None
    if email and '@' in email and not email.endswith('.local'):
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            user = User.objects.filter(username__iexact=email).first()

    if not user:
        username = _username_for_profile(profile)
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(
                username=username,
                email=email if email and not email.endswith('.local') else '',
                password=User.objects.make_random_password(length=32),
                first_name=profile.get('first_name', ''),
                last_name=profile.get('last_name', ''),
            )
            user.is_customer = True
            user.role = 'customer'
            user.is_verified = True
            user.save()

    SocialAccount.objects.update_or_create(
        provider=provider,
        provider_user_id=provider_user_id,
        defaults={
            'user': user,
            'email': email,
            'extra_data': profile,
        },
    )
    return user, True


@api_view(['POST'])
@permission_classes([AllowAny])
def social_login(request):
    provider = (request.data.get('provider') or '').lower().strip()
    if provider not in SUPPORTED_PROVIDERS:
        return Response(
            {'detail': f'Unsupported provider. Use one of: {", ".join(sorted(SUPPORTED_PROVIDERS))}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    access_token = request.data.get('access_token', '')
    id_token = request.data.get('id_token', '')

    try:
        profile = verify_social_token(
            provider,
            access_token=access_token,
            id_token=id_token,
        )
        user, _created = _get_or_create_user_from_profile(profile)
    except SocialAuthError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({'detail': 'Social login failed.'}, status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)
    return Response(_auth_payload(user, refresh), status=status.HTTP_200_OK)
