"""
Authentication and authorization middleware for the Identity module.
"""

from django.urls import resolve
from django.http import JsonResponse
from .route_access import (
    grants_module_access,
    module_for_app,
    permission_set_for_user,
)


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
    """
    Coarse route access control (Fail-Closed).

    Decides only whether an authenticated user may reach a route family, using
    the authoritative permission model (``hr.Role.permissions``). Per-operation
    and per-record authorization belongs to each module's own authorization
    layer, which runs after this gate.
    """

    # Paths that are entirely public or handled by other systems
    EXEMPT_PATHS = [
        "/api/v2/auth/",  # Login/Token endpoints
        "/api/v2/portal/auth/",  # Portal login
        "/api/v2/portal/public/",  # Public job listings (portal module)
        "/api/v2/recruitment/public/",  # Public job listings/applications (recruitment module)
        "/api/v2/health/",  # Docker/K8s health checks
        "/admin/",  # Django admin (has its own auth system)
        "/__reload__/",  # Dev tool
    ]

    # Path families that are a personal resource, not a module capability -
    # every authenticated user needs their own, regardless of role or which
    # business modules (procurement, accounts, hr, ...) their role grants
    # anything in. Gated on ``portal.*``-style permissions the coarse check
    # below requires, an ordinary employee/accounts/GM/director/procurement
    # actor holding only procurement.purchase_request.* permissions (the
    # normal case) could never reach their own notifications at all - only
    # an actor who happened to also be granted some portal permission could
    # (see F27's "notification visibility" fix). Handled the same way
    # /media/ already is below: authentication is still required, but the
    # per-module RBAC check is bypassed - the view itself (and the
    # notification repository underneath it) already scopes strictly to the
    # caller's own employee_id, so nothing here widens who can read whose
    # notifications.
    PERSONAL_RESOURCE_PATHS = [
        "/api/v2/portal/notifications",
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

        # 2b. Personal resources (e.g. notifications): same "require auth,
        # bypass the coarse per-module RBAC check" treatment as /media/ above,
        # and for the same reason - these are the caller's own data, not a
        # business-module capability, so no role/permission is the "right"
        # one to gate them on.
        if any(path.startswith(p) for p in self.PERSONAL_RESOURCE_PATHS):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {"detail": "Authentication credentials were not provided."},
                    status=401,
                )
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

            # 4. Resolve the URL to the route family it belongs to
            try:
                resolver_match = resolve(path)
                app_name = resolver_match.app_name or ""
                url_name = resolver_match.url_name or ""

                # Fail-closed: If URL has no name, we can't verify permissions safely
                if not app_name or not url_name:
                    return JsonResponse({"detail": "Permission denied."}, status=403)
            except Exception:
                # FAIL-CLOSED: If URL doesn't exist or can't be resolved, deny.
                return JsonResponse({"detail": "Permission denied."}, status=403)

            # 5. Load the user's permissions (Fail-Closed)
            try:
                permissions = permission_set_for_user(request.user)
            except Exception:
                # FAIL-CLOSED: If we can't determine permissions, deny access.
                return JsonResponse(
                    {"detail": "Unable to determine user permissions."}, status=403
                )

            if permissions is None:
                return JsonResponse({"detail": "Permission denied."}, status=403)

            # 6. Coarse check: does the user hold anything in this module?
            if grants_module_access(permissions, module_for_app(app_name)):
                return self.get_response(request)

            # FAIL-CLOSED: Deny if no permission covers this route family
            return JsonResponse(
                {"detail": "You do not have permission to access this resource."},
                status=403,
            )

        # 7. Non-API, non-admin, non-media paths pass through (e.g., root '/')
        return self.get_response(request)


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
