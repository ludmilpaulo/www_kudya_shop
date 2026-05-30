"""Verify OAuth tokens from mobile social providers."""
import logging
from typing import TypedDict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SocialProfile(TypedDict, total=False):
    provider: str
    provider_user_id: str
    email: str
    first_name: str
    last_name: str
    avatar_url: str


class SocialAuthError(Exception):
    pass


def _google_client_ids() -> set[str]:
    raw = getattr(settings, 'GOOGLE_OAUTH_CLIENT_IDS', '') or ''
    return {x.strip() for x in raw.split(',') if x.strip()}


def verify_google(*, access_token: str = '', id_token: str = '') -> SocialProfile:
    token = id_token or access_token
    if not token:
        raise SocialAuthError('Google id_token or access_token required.')

    if id_token:
        resp = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': id_token},
            timeout=15,
        )
    else:
        resp = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=15,
        )
    if resp.status_code != 200:
        raise SocialAuthError('Invalid Google token.')

    data = resp.json()
    if id_token:
        sub = data.get('sub')
    else:
        sub = data.get('id') or data.get('sub')
    allowed = _google_client_ids()
    if allowed and data.get('aud') not in allowed and data.get('azp') not in allowed:
        raise SocialAuthError('Google token audience mismatch.')

    name = (data.get('name') or '').strip()
    parts = name.split(' ', 1) if name else ['', '']
    return {
        'provider': 'google',
        'provider_user_id': str(sub or ''),
        'email': (data.get('email') or '').lower(),
        'first_name': parts[0],
        'last_name': parts[1] if len(parts) > 1 else '',
        'avatar_url': data.get('picture', ''),
    }


def verify_facebook(access_token: str) -> SocialProfile:
    if not access_token:
        raise SocialAuthError('Facebook access_token required.')

    app_id = getattr(settings, 'FACEBOOK_APP_ID', '')
    app_secret = getattr(settings, 'FACEBOOK_APP_SECRET', '')
    if app_id and app_secret:
        debug = requests.get(
            'https://graph.facebook.com/debug_token',
            params={
                'input_token': access_token,
                'access_token': f'{app_id}|{app_secret}',
            },
            timeout=15,
        )
        if debug.status_code != 200 or not debug.json().get('data', {}).get('is_valid'):
            raise SocialAuthError('Invalid Facebook token.')

    me = requests.get(
        'https://graph.facebook.com/me',
        params={'fields': 'id,name,email,picture', 'access_token': access_token},
        timeout=15,
    )
    if me.status_code != 200:
        raise SocialAuthError('Could not load Facebook profile.')

    data = me.json()
    name = (data.get('name') or '').strip()
    parts = name.split(' ', 1) if name else ['', '']
    picture = ''
    if isinstance(data.get('picture'), dict):
        picture = data['picture'].get('data', {}).get('url', '')

    return {
        'provider': 'facebook',
        'provider_user_id': str(data.get('id', '')),
        'email': (data.get('email') or '').lower(),
        'first_name': parts[0],
        'last_name': parts[1] if len(parts) > 1 else '',
        'avatar_url': picture,
    }


def verify_instagram(access_token: str) -> SocialProfile:
    if not access_token:
        raise SocialAuthError('Instagram access_token required.')

    resp = requests.get(
        'https://graph.instagram.com/me',
        params={'fields': 'id,username', 'access_token': access_token},
        timeout=15,
    )
    if resp.status_code != 200:
        raise SocialAuthError('Invalid Instagram token.')

    data = resp.json()
    username = data.get('username') or data.get('id')
    return {
        'provider': 'instagram',
        'provider_user_id': str(data.get('id', '')),
        'email': f'{username}@instagram.local' if username else '',
        'first_name': username or 'Instagram',
        'last_name': 'User',
        'avatar_url': '',
    }


def verify_tiktok(access_token: str) -> SocialProfile:
    if not access_token:
        raise SocialAuthError('TikTok access_token required.')

    headers = {'Authorization': f'Bearer {access_token}'}
    resp = requests.get(
        'https://open.tiktokapis.com/v2/user/info/',
        params={'fields': 'open_id,union_id,avatar_url,display_name'},
        headers=headers,
        timeout=15,
    )
    if resp.status_code != 200:
        raise SocialAuthError('Invalid TikTok token.')

    payload = resp.json()
    user = (payload.get('data') or {}).get('user') or {}
    open_id = str(user.get('open_id') or user.get('union_id') or '')
    if not open_id:
        raise SocialAuthError('TikTok profile missing open_id.')

    display = (user.get('display_name') or 'TikTok User').strip()
    parts = display.split(' ', 1)
    return {
        'provider': 'tiktok',
        'provider_user_id': open_id,
        'email': f'{open_id}@tiktok.local',
        'first_name': parts[0],
        'last_name': parts[1] if len(parts) > 1 else '',
        'avatar_url': user.get('avatar_url', ''),
    }


def verify_social_token(provider: str, *, access_token: str = '', id_token: str = '') -> SocialProfile:
    provider = (provider or '').lower().strip()
    verifiers = {
        'google': lambda: verify_google(access_token=access_token, id_token=id_token),
        'facebook': lambda: verify_facebook(access_token),
        'instagram': lambda: verify_instagram(access_token),
        'tiktok': lambda: verify_tiktok(access_token),
    }
    fn = verifiers.get(provider)
    if not fn:
        raise SocialAuthError(f'Unsupported provider: {provider}')
    profile = fn()
    if not profile.get('provider_user_id'):
        raise SocialAuthError('Provider user id missing.')
    return profile
