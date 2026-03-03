# yourapp/middleware.py

from django.urls import resolve
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from .permissions import ROLE_PERMISSIONS
import fnmatch

# JWT Authentication Middleware - processes JWT tokens before RBAC
class JWTAuthenticationMiddleware:
    """
    Middleware to authenticate users via JWT tokens.
    This must run AFTER Django's AuthenticationMiddleware but BEFORE RBACMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip if user is already authenticated via session
        if request.user.is_authenticated:
            return self.get_response(request)

        # Try to authenticate via JWT
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            try:
                from rest_framework_simplejwt.authentication import JWTAuthentication
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                user = jwt_auth.get_user(validated_token)
                request.user = user
            except Exception:
                # Token invalid or expired - let the view handle 401
                pass

        return self.get_response(request)


class RBACMiddleware:
    # Paths that should always be allowed (public or auth-related)
    EXEMPT_PATHS = [
        '/api/auth/',
        '/api/portal/auth/',  # Employee portal authentication
        '/admin/',
        '/__reload__/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow unauthenticated requests (let view handle auth)
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Check exempt paths
        for exempt_path in self.EXEMPT_PATHS:
            if request.path.startswith(exempt_path):
                return self.get_response(request)

        try:
            resolver_match = resolve(request.path)
            app_name = resolver_match.app_name or ''
            url_name = resolver_match.url_name or ''
            view_perm = f"{app_name}.{url_name}"
        except Exception:
            # If we can't resolve the path, allow it through
            return self.get_response(request)

        # Get user role - handle both CustomUser.role and Employee.role
        user_role = getattr(request.user, 'role', None)

        if user_role is None:
            # Try to get role from employee profile
            employee = getattr(request.user, 'employee_profile', None)
            if employee:
                role_obj = getattr(employee, 'role', None)
                user_role = getattr(role_obj, 'name', 'STAFF') if role_obj else 'STAFF'
            else:
                user_role = 'STAFF'

        # Normalize role name: uppercase and replace spaces with underscores
        if user_role:
            user_role = user_role.upper().replace(' ', '_').replace('-', '_')

        allowed_perms = ROLE_PERMISSIONS.get(user_role, [])

        # Check permissions with wildcard support
        if self._has_permission(view_perm, allowed_perms, app_name):
            return self.get_response(request)

        # Return 403 JSON response instead of raising exception
        return JsonResponse(
            {"detail": "You do not have permission to access this resource."},
            status=403
        )

    def _has_permission(self, view_perm, allowed_perms, app_name):
        """Check if the view permission matches any allowed permission pattern."""
        for perm in allowed_perms:
            # Full wildcard access
            if perm == "*":
                return True

            # App-level wildcard (e.g., "hr.*" matches "hr.dashboard")
            if perm.endswith(".*"):
                perm_app = perm[:-2]  # Remove ".*"
                if app_name and (app_name == perm_app or app_name.startswith(perm_app)):
                    return True
                # Also check if view_perm starts with the app name
                if view_perm.startswith(perm_app + "."):
                    return True

            # Exact match
            if perm == view_perm:
                return True

            # Fnmatch pattern matching
            if fnmatch.fnmatch(view_perm, perm):
                return True

        return False
