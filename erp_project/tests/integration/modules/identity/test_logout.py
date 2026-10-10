"""
Synergy logout revokes its refresh token (INT-01; same mechanism as B3).

Before, synergy logout only cleared localStorage, so the refresh token stayed
valid for up to 30 days. Now POST /api/v2/auth/logout/ with the refresh token:
- blacklists it if it belongs to the caller, and the refresh endpoint then
  refuses it;
- leaves another user's token alone;
- always returns 200, so the client can always finish logging out.

Requests carry a real JWT, so they pass through RBACMiddleware.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

User = get_user_model()

LOGOUT_URL = "/api/v2/auth/logout/"
REFRESH_URL = "/api/v2/auth/token/refresh/"

_numbers = count(1)


def make_user(**extra):
    return User.objects.create_user(
        email=f"logout{next(_numbers)}@zchpc.test", password="Str0ng-Passw0rd", **extra
    )


def logout(user, refresh):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client.post(LOGOUT_URL, {"refresh": refresh}, format="json")


def refresh(token):
    return APIClient().post(REFRESH_URL, {"refresh": token}, format="json")


def test_logout_revokes_the_callers_refresh_token():
    user = make_user()  # no role, no permissions
    token = str(RefreshToken.for_user(user))

    response = logout(user, token)

    assert response.status_code == status.HTTP_200_OK
    assert refresh(token).status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_leaves_another_users_token_alone():
    caller, other = make_user(), make_user()
    others_token = str(RefreshToken.for_user(other))

    response = logout(caller, others_token)

    assert response.status_code == status.HTTP_200_OK
    assert refresh(others_token).status_code == status.HTTP_200_OK


@pytest.mark.parametrize("body", [None, "not-a-token"])
def test_logout_without_a_usable_token_still_returns_200(body):
    assert logout(make_user(), body).status_code == status.HTTP_200_OK


def test_logout_requires_authentication():
    response = APIClient().post(LOGOUT_URL, {"refresh": "x"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_a_user_holding_a_temporary_password_can_log_out():
    """REM-07 confinement must not stop a logout."""
    user = make_user(must_change_password=True)
    token = str(RefreshToken.for_user(user))

    assert logout(user, token).status_code == status.HTTP_200_OK
    assert refresh(token).status_code == status.HTTP_401_UNAUTHORIZED
