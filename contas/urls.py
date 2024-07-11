from django.urls import path
from .views import (
    PasswordResetConfirmView,
    ActivateAccountView,
    CustomAuthToken,
    LogoutView,
    PasswordResetView,
)

urlpatterns = [
    path("reset-password/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "reset-password-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "activate-account/<str:uidb64>/<str:token>/",
        ActivateAccountView.as_view(),
        name="activate_account",
    ),
    path("login/", CustomAuthToken.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
