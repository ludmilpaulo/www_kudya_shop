from django.urls import path
from . import api_views
from . import social_views

urlpatterns = [
    path('register/', api_views.register, name='api-register'),
    path('login/', api_views.login, name='api-login'),
    path('social/', social_views.social_login, name='api-social-login'),
    path('logout/', api_views.logout, name='api-logout'),
    path('refresh/', api_views.refresh_token, name='api-refresh'),
    path('me/', api_views.me, name='api-me'),
]
