from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from .models import Membership


def user_has_roles(user, org, roles):
    if not user.is_authenticated or not org:
        return False
    return Membership.objects.filter(
        user=user, organization=org, role__in=roles, is_active=True
    ).exists()


def require_roles(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not user_has_roles(request.user, getattr(request, "current_org", None), roles):
                if not request.user.is_authenticated:
                    return redirect("signin")
                return HttpResponseForbidden("No autorizado")
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
