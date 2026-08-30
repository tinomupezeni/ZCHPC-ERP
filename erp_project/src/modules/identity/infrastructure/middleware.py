"""
Authentication and authorization middleware for the Identity module.
"""

from django.urls import resolve
from django.http import JsonResponse
from .permissions import ROLE_PERMISSIONS
import fnmatch


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
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
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
    """Role-Based Access Control middleware (Fail-Closed)."""

    # Paths that are entirely public or handled by other systems
    EXEMPT_PATHS = [
        "/api/v2/auth/",  # Login/Token endpoints
        "/api/v2/portal/auth/",  # Portal login
        "/api/v2/portal/public/",  # Public job listings
        "/api/v2/health/",  # Docker/K8s health checks
        "/admin/",  # Django admin (has its own auth system)
        "/__reload__/",  # Dev tool
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def _is_exempt(self, path):
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        # Static files (CSS/JS/Images) are public.
        # Note: /media/ is intentionally NOT here to protect sensitive docs.
        if path.startswith("/static/"):
            return True
        return False

    def __call__(self, request):
        path = request.path

        # 1. Allow fully public/system paths
        if self._is_exempt(path):
            return self.get_response(request)

        # 2. Handle /media/ specifically (Require auth, but bypass strict RBAC roles)
        # This allows employees to download their own payslips without needing 'HR' role.
        if path.startswith("/media/"):
            if not request.user.is_authenticated:
                return JsonResponse({"detail": "Authentication required."}, status=401)
            return self.get_response(request)

        # 3. FAIL-CLOSED: For all other API paths, enforce authentication immediately
        if path.startswith("/api/"):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {"detail": "Authentication credentials were not provided."},
                    status=401,
                )

            # Superusers bypass application RBAC (intentional privileged bypass)
            if request.user.is_superuser:
                return self.get_response(request)

            # 4. Resolve URL to permission string
            try:
                resolver_match = resolve(path)
                app_name = resolver_match.app_name or ""
                url_name = resolver_match.url_name or ""

                # Fail-closed: If URL has no name, we can't verify permissions safely
                if not app_name or not url_name:
                    return JsonResponse({"detail": "Permission denied."}, status=403)

                view_perm = f"{app_name}.{url_name}"
            except Exception:
                # FAIL-CLOSED: If URL doesn't exist or can't be resolved, deny.
                return JsonResponse({"detail": "Permission denied."}, status=403)

            # 5. Get user role (Fail-Closed)
            user_role = getattr(request.user, "role", None)
            if user_role is None:
                try:
                    employee = request.user.employee_profile
                    if employee:
                        role_obj = getattr(employee, "role", None)
                        user_role = (
                            getattr(role_obj, "name", None) if role_obj else None
                        )
                except Exception:
                    # FAIL-CLOSED: If we can't determine the role, deny access.
                    return JsonResponse(
                        {"detail": "Unable to determine user permissions."}, status=403
                    )

            # If after all checks, user_role is still None, deny.
            if not user_role:
                return JsonResponse({"detail": "Permission denied."}, status=403)

            # Normalize role name
            user_role = user_role.upper().replace(" ", "_").replace("-", "_")
            allowed_perms = ROLE_PERMISSIONS.get(user_role, [])

            # 6. Check permissions
            if self._has_permission(view_perm, allowed_perms, app_name):
                return self.get_response(request)

            # FAIL-CLOSED: Deny if no explicit permission
            return JsonResponse(
                {"detail": "You do not have permission to access this resource."},
                status=403,
            )

        # 7. Non-API, non-admin, non-media paths pass through (e.g., root '/')
        return self.get_response(request)

    def _has_permission(self, view_perm, allowed_perms, app_name):
        """Check if the view permission matches any allowed permission pattern."""
        for perm in allowed_perms:
            if perm == "*":
                return True

            if perm.endswith(".*"):
                perm_app = perm[:-2]
                if app_name and (app_name == perm_app or app_name.startswith(perm_app)):
                    return True
                if view_perm.startswith(perm_app + "."):
                    return True

            if perm == view_perm:
                return True

            if fnmatch.fnmatch(view_perm, perm):
                return True

        return False


class ModuleAccessMiddleware:
    """
    Middleware to restrict access to modules that are not active.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check API v2 paths
        if not request.path.startswith('/api/v2/'):
            return self.get_response(request)

        # Exempt paths
        exempt_paths = [
            '/api/v2/auth/',
            '/api/v2/portal/auth/',
            '/api/v2/portal/public/',
        ]
        for path in exempt_paths:
            if request.path.startswith(path):
                return self.get_response(request)

        # Determine which module is being accessed
        # Path format: /api/v2/{module_name}/...
        parts = request.path.split('/')
        if len(parts) < 4:
            return self.get_response(request)
            
        module_identifier = parts[3]
        
        # Check if the module is active in the database
        try:
            from modules.identity.infrastructure.persistence.models import SystemModule
            module = SystemModule.objects.filter(identifier=module_identifier).first()
            
            # If the module is registered but inactive, block access
            if module and not module.is_active:
                return JsonResponse(
                    {"detail": f"The '{module.name}' module is not installed."},
                    status=403
                )
        except Exception:
            # If something goes wrong, allow for now
            pass

        return self.get_response(request)
