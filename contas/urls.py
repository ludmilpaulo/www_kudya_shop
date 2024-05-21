from django.urls import path
from .views import ResetPasswordView, PasswordResetConfirmView, ActivateAccountView, CustomAuthToken, LogoutView

urlpatterns = [
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('reset-password-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('activate-account/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate_account'),
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
