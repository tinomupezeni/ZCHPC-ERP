from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")

            if request.user.role not in allowed_roles:
                raise PermissionDenied("You do not have access to this resource")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
