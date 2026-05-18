from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import SupportTicket
from .serializers import SupportTicketAdminSerializer, SupportTicketSerializer
from contas.permissions import IsSupportAdmin, user_has_any_role, scope_queryset_for_user


class SupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return SupportTicketAdminSerializer
        return SupportTicketSerializer

    def get_queryset(self):
        if user_has_any_role(
            self.request.user,
            'super_admin',
            'country_admin',
            'city_admin',
            'support',
        ):
            return scope_queryset_for_user(
                self.request.user,
                SupportTicket.objects.all(),
                country_lookup='user__country',
                city_lookup='user__city',
            )
        return SupportTicket.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            return [IsSupportAdmin()]
        return [IsAuthenticated()]
