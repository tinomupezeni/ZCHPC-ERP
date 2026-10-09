"""
B3: portal session refresh and logout.

Before B3 the portal refreshed against /api/v2/portal/auth/refresh/, which
does not exist (404), so users were logged out when the access token
expired; and portal logout returned 400 because token.blacklist() needs
rest_framework_simplejwt.token_blacklist, which was not installed.

Now:
- a portal login's refresh token refreshes at /api/v2/auth/token/refresh/;
- portal logout always returns 200 and blacklists the caller's refresh
  token, which the refresh endpoint then refuses;
- logout never revokes another user's refresh token.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from modules.hr.infrastructure.persistence.models import Employees

pytestmark = pytest.mark.django_db

User = get_user_model()

PORTAL_LOGIN_URL = "/api/v2/portal/auth/login/"
PORTAL_LOGOUT_URL = "/api/v2/portal/auth/logout/"
PORTAL_ME_URL = "/api/v2/portal/auth/me/"
REFRESH_URL = "/api/v2/auth/token/refresh/"
PASSWORD = "Str0ng-Initial-Passw0rd"

_numbers = count(73001)


def make_employee(label):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password=PASSWORD)
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, employee_id=f"EMP{n}",
    )


def portal_login(employee):
    response = APIClient().post(
        PORTAL_LOGIN_URL,
        {"ec_number": employee.employee_id, "password": PASSWORD},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    return response.data


def bearer(access):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


def refresh(token):
    return APIClient().post(REFRESH_URL, {"refresh": token}, format="json")


class TestPortalRefresh:
    def test_portal_refresh_token_refreshes_at_the_identity_endpoint(self):
        tokens = portal_login(make_employee("Rhoda"))

        response = refresh(tokens["refresh"])

        assert response.status_code == status.HTTP_200_OK
        assert bearer(response.data["access"]).get(PORTAL_ME_URL).status_code == status.HTTP_200_OK

    def test_the_old_portal_refresh_path_does_not_exist(self):
        tokens = portal_login(make_employee("Olga"))

        response = APIClient().post(
            "/api/v2/portal/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPortalLogout:
    def test_logout_returns_200_and_the_refresh_token_is_refused_afterwards(self):
        tokens = portal_login(make_employee("Lola"))

        response = bearer(tokens["access"]).post(
            PORTAL_LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert refresh(tokens["refresh"]).status_code == status.HTTP_401_UNAUTHORIZED

    def test_logging_out_twice_still_returns_200(self):
        tokens = portal_login(make_employee("Tess"))
        client = bearer(tokens["access"])

        client.post(PORTAL_LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json")
        response = client.post(PORTAL_LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize("body", [{}, {"refresh": ""}, {"refresh": "not-a-jwt"}])
    def test_logout_without_a_usable_refresh_token_returns_200(self, body):
        tokens = portal_login(make_employee("Nina"))

        response = bearer(tokens["access"]).post(PORTAL_LOGOUT_URL, body, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert refresh(tokens["refresh"]).status_code == status.HTTP_200_OK

    def test_logout_does_not_revoke_another_users_refresh_token(self):
        caller = portal_login(make_employee("Cara"))
        victim = make_employee("Vera")
        victims_refresh = str(RefreshToken.for_user(victim.user))

        response = bearer(caller["access"]).post(
            PORTAL_LOGOUT_URL, {"refresh": victims_refresh}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert refresh(victims_refresh).status_code == status.HTTP_200_OK

    def test_logout_requires_authentication(self):
        tokens = portal_login(make_employee("Ursa"))

        response = APIClient().post(PORTAL_LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert refresh(tokens["refresh"]).status_code == status.HTTP_200_OK
