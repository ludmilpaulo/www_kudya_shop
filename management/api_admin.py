"""Lightweight admin dashboard stats API."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from contas.permissions import IsScopedPlatformAdmin, scope_queryset_for_user


@api_view(['GET'])
@permission_classes([IsScopedPlatformAdmin])
def admin_dashboard(request):
    from order.models import Order
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)
    scoped_orders = scope_queryset_for_user(
        request.user,
        Order.objects.all(),
        country_lookup='customer__user__country',
        city_lookup='customer__user__city',
    )

    data = {
        'orders_today': scoped_orders.filter(created_at__date=today).count(),
        'orders_week': scoped_orders.filter(created_at__gte=week_ago).count(),
    }
    try:
        from rides.models import Ride
        scoped_rides = scope_queryset_for_user(
            request.user,
            Ride.objects.all(),
            country_lookup='country',
            city_lookup='city',
        )
        data['rides_today'] = scoped_rides.filter(created_at__date=today).count()
        data['rides_active'] = scoped_rides.filter(status__in=['accepted', 'in_progress', 'arrived']).count()
    except Exception:
        data['rides_today'] = 0
        data['rides_active'] = 0
    try:
        from deliveries.models import PackageDelivery
        scoped_deliveries = scope_queryset_for_user(
            request.user,
            PackageDelivery.objects.all(),
            country_lookup='customer__country',
            city_lookup='customer__city',
        )
        data['deliveries_today'] = scoped_deliveries.filter(created_at__date=today).count()
    except Exception:
        data['deliveries_today'] = 0
    try:
        from drivers.models import Driver
        scoped_drivers = scope_queryset_for_user(
            request.user,
            Driver.objects.all(),
            country_lookup='user__country',
            city_lookup='user__city',
        )
        data['active_drivers'] = scoped_drivers.filter(is_online=True).count()
    except Exception:
        data['active_drivers'] = 0
    try:
        from contas.models import User
        scoped_users = scope_queryset_for_user(
            request.user,
            User.objects.all(),
            country_lookup='country',
            city_lookup='city',
        )
        data['total_users'] = scoped_users.count()
    except Exception:
        data['total_users'] = 0
    return Response(data)
