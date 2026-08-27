"""
Security regression tests for the Identity module.

These tests verify the fail-closed security requirements for:

    - Django DEBUG defaults
    - CORS defaults
    - DRF authentication defaults
    - RBAC authentication enforcement
    - RBAC permission enforcement
    - Public/system endpoint exemptions
    - Protected media access

These tests are intended to prevent the reintroduction of the security
issues identified during the ERP backend security review.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class SecurityDefaultsTest(TestCase):
    """Verify that security-sensitive settings fail closed."""

    def test_debug_is_disabled_by_default(self):
        """DEBUG must not default to True."""
        self.assertFalse(
            settings.DEBUG,
            "Security Risk: DEBUG is enabled. "
            "Production must default to DEBUG=False.",
        )

    def test_cors_is_not_wildcard_by_default(self):
        """CORS must not allow every origin by default."""
        self.assertFalse(
            settings.CORS_ALLOW_ALL_ORIGINS,
            "Security Risk: CORS_ALLOW_ALL_ORIGINS is True. "
            "CORS must default to a restricted allowlist.",
        )

    def test_cors_credentials_are_disabled_by_default(self):
        """
        Credentialed cross-origin requests must not be enabled by default.

        This is appropriate when the application uses JWTs in the
        Authorization header rather than cross-origin cookies.
        """
        self.assertFalse(
            settings.CORS_ALLOW_CREDENTIALS,
            "Security Risk: CORS_ALLOW_CREDENTIALS is enabled by default.",
        )

    def test_drf_requires_authentication_by_default(self):
        """
        DRF must require authentication unless a view explicitly overrides
        the default permission policy.
        """
        default_permissions = settings.REST_FRAMEWORK.get(
            "DEFAULT_PERMISSION_CLASSES",
            [],
        )

        self.assertIn(
            "rest_framework.permissions.IsAuthenticated",
            default_permissions,
            "Security Risk: DRF does not require authentication by default.",
        )


class RBACFailClosedTest(TestCase):
    """
    Verify that RBAC denies access when authentication or authorization
    cannot be established safely.
    """

    PROTECTED_API_PATH = "/api/v2/hr/employees/"
    HEALTH_PATH = "/api/v2/health/"
    MEDIA_PATH = "/media/fake_document.pdf"

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="testuser@zchpc.ac.zw",
            password="securepassword123",
        )

    def _authenticate_as_user(self):
        """
        Authenticate using a real JWT token.

        This is preferred over force_authenticate() because the security
        behavior being tested includes middleware, which runs before DRF
        view-level authentication helpers.
        """
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_anonymous_protected_api_request_is_rejected(self):
        """
        Unauthenticated requests to protected API endpoints must receive 401.
        """
        response = self.client.get(self.PROTECTED_API_PATH)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            (
                "Fail-Open Bug: An unauthenticated request was allowed "
                f"through {self.PROTECTED_API_PATH}."
            ),
        )

    def test_invalid_token_is_rejected(self):
        """
        Requests with invalid JWT tokens must receive 401.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")

        response = self.client.get(self.PROTECTED_API_PATH)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Fail-Open Bug: An invalid JWT token was accepted.",
        )

    def test_anonymous_media_request_is_rejected(self):
        """
        Media files must not be publicly accessible through the RBAC layer.
        """
        response = self.client.get(self.MEDIA_PATH)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            (
                "Security Risk: An unauthenticated request was allowed "
                "through /media/."
            ),
        )

    def test_health_endpoint_is_public(self):
        """
        The health endpoint must remain accessible without authentication.

        This is required for Docker/Kubernetes health checks.
        """
        response = self.client.get(self.HEALTH_PATH)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "Health endpoint is unexpectedly protected.",
        )

    def test_authenticated_request_is_not_rejected_as_anonymous(self):
        """
        A successfully authenticated user must not receive 401 merely
        because the RBAC middleware cannot find a JWT in the request.

        The endpoint may still return 403 if the user lacks the required
        application permission.
        """
        self._authenticate_as_user()

        response = self.client.get(self.PROTECTED_API_PATH)

        self.assertNotEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Authentication Bug: An authenticated user was treated as anonymous.",
        )

    def test_authenticated_user_without_required_permission_is_rejected(self):
        """
        An authenticated user who has no applicable RBAC permission must
        receive 403 rather than being allowed through.

        This test intentionally uses a newly-created user whose role/
        permissions have not been granted.
        """
        self._authenticate_as_user()

        response = self.client.get(self.PROTECTED_API_PATH)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            (
                "Fail-Open Bug: An authenticated user without an applicable "
                "RBAC permission was allowed to access the protected endpoint."
            ),
        )

    def test_unknown_role_does_not_grant_access(self):
        """
        A user with an unknown role must receive 403.

        Unknown roles must resolve to no permissions rather than gaining
        access through a permissive fallback.

        Note:
        This test only runs if CustomUser has a concrete `role` field.
        In many ERP setups, role is stored on Employee or employee_profile,
        not directly on CustomUser.
        """
        try:
            role_field = User._meta.get_field("role")
        except Exception:
            self.skipTest(
                "CustomUser does not have a concrete 'role' field. "
                "Role is probably stored on an employee profile or related object. "
                "Update this test after confirming where role is stored."
            )

        if getattr(role_field, "is_relation", False):
            self.skipTest(
                "CustomUser.role is a relationship field. "
                "Create the related Role object instead of assigning a plain string."
            )

        self.user.role = "NON_EXISTENT_SECURITY_ROLE"
        self.user.save(update_fields=["role"])

        self._authenticate_as_user()

        response = self.client.get(self.PROTECTED_API_PATH)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            (
                "Fail-Open Bug: An unknown role was granted access "
                "to a protected endpoint."
            ),
        )


class PublicEndpointTest(TestCase):
    """Verify that intentionally public endpoints remain accessible."""

    def setUp(self):
        self.client = APIClient()

    def test_authentication_endpoint_is_not_blocked_by_rbac(self):
        """
        Authentication endpoints must remain outside the protected RBAC
        permission flow.

        The exact response depends on the endpoint implementation, so this
        test only verifies that RBAC does not return its authentication
        failure response.
        """
        response = self.client.post(
            "/api/v2/auth/",
            {},
            format="json",
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            (
                "RBAC unexpectedly blocked an authentication endpoint. "
                "Verify the actual authentication URL if this fails."
            ),
        )


class StaticAndMediaAccessTest(TestCase):
    """
    Verify the intended distinction between public static assets and
    protected media.
    """

    def setUp(self):
        self.client = APIClient()

    def test_static_path_is_not_blocked_by_rbac(self):
        """
        Static assets are intentionally exempt from RBAC.
        """
        response = self.client.get("/static/test.css")

        # The file may not exist, so 404 is acceptable. What matters is
        # that RBAC does not reject the request with 401/403.
        self.assertNotIn(
            response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
            (
                "RBAC unexpectedly blocked a static asset request. "
                "Static files should be exempt from RBAC."
            ),
        )

    def test_media_requires_authentication(self):
        """
        Media requests must require authentication before reaching the
        media-serving layer.
        """
        response = self.client.get("/media/test-document.pdf")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Unauthenticated media access was not rejected.",
        )

class CorsWhitelistTest(TestCase):
    """Verify CORS is explicitly whitelisted."""

    def test_cors_does_not_use_wildcard(self):
        self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)

    def test_cors_origins_do_not_contain_wildcard(self):
        self.assertNotIn(
            "*",
            settings.CORS_ALLOWED_ORIGINS,
            "Security Risk: CORS_ALLOWED_ORIGINS contains a wildcard.",
        )

    def test_cors_origins_are_valid_urls(self):
        for origin in settings.CORS_ALLOWED_ORIGINS:
            self.assertTrue(
                origin.startswith("http://") or origin.startswith("https://"),
                f"Invalid CORS origin: {origin}",
            )