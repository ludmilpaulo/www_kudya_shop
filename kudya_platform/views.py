from django.db import models
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import City, Translation, PlatformModule, CountryComplianceSetting, AuditEvent
from .serializers import (
    CitySerializer,
    TranslationSerializer,
    PlatformModuleSerializer,
    CountryComplianceSettingSerializer,
    AuditEventSerializer,
)
from contas.permissions import IsScopedPlatformAdmin, scope_queryset_for_user


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.filter(is_active=True).select_related('country')
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    filterset_fields = ['country']


@api_view(['GET'])
@permission_classes([AllowAny])
def translations_bundle(request):
    """Return all translations for a language/module as key-value dict."""
    language = request.query_params.get('lang', 'en')
    module = request.query_params.get('module')
    qs = Translation.objects.filter(language__in=['en', language], is_active=True)
    if module:
        qs = qs.filter(module=module)
    bundle = {}
    for item in qs.filter(language='en'):
        bundle[item.key] = item.value
    for item in qs.filter(language=language):
        bundle[item.key] = item.value
    return Response(bundle)


@api_view(['GET'])
@permission_classes([AllowAny])
def home_modules(request):
    """Super-app home service cards."""
    language = request.query_params.get('lang', 'en')
    country_id = request.query_params.get('country')
    qs = PlatformModule.objects.filter(is_active=True)
    if country_id:
        qs = qs.filter(
            models.Q(allowed_countries__isnull=True) |
            models.Q(allowed_countries__id=country_id)
        ).distinct()
    serializer = PlatformModuleSerializer(
        qs, many=True, context={'language': language, 'request': request}
    )
    return Response(serializer.data)


class CountryComplianceSettingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CountryComplianceSetting.objects.filter(is_active=True).select_related('country')
    serializer_class = CountryComplianceSettingSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['country']


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditEventSerializer
    permission_classes = [IsScopedPlatformAdmin]
    filterset_fields = ['action', 'target_type', 'country', 'city']

    def get_queryset(self):
        qs = AuditEvent.objects.select_related('actor', 'country', 'city')
        return scope_queryset_for_user(
            self.request.user,
            qs,
            country_lookup='country',
            city_lookup='city',
        )
