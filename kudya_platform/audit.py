from .models import AuditEvent


def record_audit_event(
    request,
    *,
    action,
    target,
    country=None,
    city=None,
    metadata=None,
):
    return AuditEvent.objects.create(
        actor=getattr(request, 'user', None) if getattr(request, 'user', None) and request.user.is_authenticated else None,
        action=action,
        target_type=target.__class__.__name__,
        target_id=str(getattr(target, 'pk', '') or ''),
        target_repr=str(target)[:255],
        country=country,
        city=city,
        metadata=metadata or {},
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
    )
