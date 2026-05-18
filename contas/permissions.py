from rest_framework.permissions import BasePermission


ADMIN_ROLES = {
    'super_admin',
    'country_admin',
    'city_admin',
    'support',
    'finance_admin',
    'compliance_admin',
    'safety_admin',
}

SCOPED_ADMIN_ROLES = ADMIN_ROLES - {'super_admin'}


def user_has_any_role(user, *roles):
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or getattr(user, 'role', None) in set(roles))
    )


def get_admin_scope(user):
    """Return the territory a scoped admin may manage."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser or getattr(user, 'role', None) == 'super_admin':
        return {'level': 'global', 'country_id': None, 'city_id': None}
    if getattr(user, 'role', None) not in SCOPED_ADMIN_ROLES:
        return None
    if getattr(user, 'role', None) == 'city_admin':
        if not getattr(user, 'city_id', None):
            return None
        return {
            'level': 'city',
            'country_id': getattr(user, 'country_id', None),
            'city_id': user.city_id,
        }
    if getattr(user, 'city_id', None):
        return {
            'level': 'city',
            'country_id': getattr(user, 'country_id', None),
            'city_id': user.city_id,
        }
    if getattr(user, 'country_id', None):
        return {
            'level': 'country',
            'country_id': user.country_id,
            'city_id': None,
        }
    return None


def user_can_access_scope(user, country_id=None, city_id=None):
    scope = get_admin_scope(user)
    if not scope:
        return False
    if scope['level'] == 'global':
        return True
    if scope['level'] == 'city':
        return city_id is not None and city_id == scope['city_id']
    if scope['level'] == 'country':
        return country_id is not None and country_id == scope['country_id']
    return False


def scope_queryset_for_user(user, queryset, *, country_lookup='country', city_lookup='city'):
    scope = get_admin_scope(user)
    if not scope:
        return queryset.none()
    if scope['level'] == 'global':
        return queryset
    if scope['level'] == 'city' and city_lookup:
        return queryset.filter(**{f'{city_lookup}_id': scope['city_id']})
    if scope['level'] == 'country' and country_lookup:
        return queryset.filter(**{f'{country_lookup}_id': scope['country_id']})
    return queryset.none()


class HasAnyRole(BasePermission):
    allowed_roles: set[str] = set()

    def has_permission(self, request, view):
        return user_has_any_role(request.user, *self.allowed_roles)


class IsPlatformAdmin(HasAnyRole):
    allowed_roles = ADMIN_ROLES


class IsComplianceAdmin(HasAnyRole):
    allowed_roles = {'super_admin', 'country_admin', 'city_admin', 'compliance_admin'}


class IsFinanceAdmin(HasAnyRole):
    allowed_roles = {'super_admin', 'country_admin', 'finance_admin'}


class IsSupportAdmin(HasAnyRole):
    allowed_roles = {'super_admin', 'country_admin', 'city_admin', 'support'}


class IsScopedPlatformAdmin(IsPlatformAdmin):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and get_admin_scope(request.user) is not None
