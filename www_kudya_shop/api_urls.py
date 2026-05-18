"""
Unified Kudya Super App API routes.
All new modules are mounted under /api/ while legacy paths remain for backward compatibility.
"""
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from management.api_admin import admin_dashboard
from doctors.urls import appointment_urlpatterns

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='api-docs'),
    # Mobility & marketplace
    path('rides/', include('rides.urls')),
    path('deliveries/', include('deliveries.urls')),
    path('rentals/', include('rentals.urls')),
    # Platform: translations, home modules, cities
    path('platform/', include('kudya_platform.urls')),
    # Healthcare
    path('doctors/', include('doctors.urls')),
    path('appointments/', include((appointment_urlpatterns, 'appointments'))),
    # Accommodation
    path('accommodation/', include('accommodation.urls')),
    # Properties (also at legacy /properties/)
    path('properties/', include('properties.urls')),
    # Professional services (legacy path aliased)
    path('services/', include('services.urls')),
    # Wallet
    path('wallet/', include('wallets.urls')),
    # Shared verification documents
    path('documents/', include('documents.api_urls')),
    # Payments
    path('payments/', include('payments.urls')),
    # Auth aliases
    path('auth/', include('contas.api_urls')),
    # Countries (from services app)
    path('countries/', include('services.country_urls')),
    # Translations shortcut
    path('translations/', include('kudya_platform.translation_urls')),
    # Support
    path('support/', include('support.urls')),
    # Driver API alias (fixes /drivers/ vs /driver/ mismatch in mobile apps)
    path('drivers/', include('drivers.urls')),
    # Admin dashboard stats
    path('admin/dashboard/', admin_dashboard),
]
