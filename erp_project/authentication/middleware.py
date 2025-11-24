# yourapp/middleware.py

from django.urls import resolve
from django.core.exceptions import PermissionDenied
from .permissions import ROLE_PERMISSIONS

class RBACMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        resolver_match = resolve(request.path)
        view_perm = f"{resolver_match.app_name}.{resolver_match.url_name}"

        user_role = request.user.role
        allowed_perms = ROLE_PERMISSIONS.get(user_role, [])

        if "*" in allowed_perms or view_perm in allowed_perms:
            return self.get_response(request)

        raise PermissionDenied("RBAC: Access denied for your role")
