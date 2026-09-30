"""
JWT authentication that honours the employee lifecycle (AUD-02).
"""

from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from modules.identity.infrastructure.account_access import employment_allows_access


class EmployeeLifecycleJWTAuthentication(JWTAuthentication):
    """
    SimpleJWT's authentication, plus the employment lifecycle.

    The parent already rejects a disabled login and a token issued under an
    earlier password on every request. This also rejects the token of a
    login whose employee is deactivated or archived, reported exactly like a
    disabled login.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not employment_allows_access(user):
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")
        return user
