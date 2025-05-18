from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .user_views import GetInviteByTokenView, SendInviteView, SignInviteView

from .signature_views import save_signed_pdf

from .signuture import SignatureViewSet

from .views import DocumentViewSet
from .invite_views import SignatureInviteViewSet
from .otp_views import SendOTPView, VerifyOTPView
from .audit_views import generate_audit_report

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='documents')
router.register(r'signatures', SignatureViewSet, basename='signatures')
router.register('invites', SignatureInviteViewSet, basename='invites')

urlpatterns = [
    path('', include(router.urls)),
    path('save-signed-pdf/', save_signed_pdf),

    # Invite someone to sign
    path('send-invite/', SendInviteView.as_view(), name='send-invite'),

    # OTP endpoints
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),

    # Audit trail PDF download
    path('audit-report/<int:document_id>/', generate_audit_report, name='audit-report'),
    
    path('invite/<str:token>/', GetInviteByTokenView.as_view(), name='get-invite-by-token'),
    path('invite/<str:token>/sign/', SignInviteView.as_view(), name='sign-invite'),
]
