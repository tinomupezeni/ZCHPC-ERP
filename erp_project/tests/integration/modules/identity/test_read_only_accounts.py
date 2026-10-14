"""
Read-only accounts (owner, Wed 2026-10-14: the evaluation admin, EMP0001, is
read-only for now).

An account listed in settings.READ_ONLY_ACCOUNTS may read everything its role
allows, but RBACMiddleware refuses every change (403 READ_ONLY_ACCOUNT) - also
for a superuser, and also in the Django admin - except signing in and out and
changing its own password. Other accounts are unaffected.

Requests carry a real JWT, so they pass through RBACMiddleware.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

User = get_user_model()

ADMIN_EMAIL = "readonly-admin@zchpc.test"
USERS_URL = "/api/v2/auth/users/"

_numbers = count(1)


def make_superuser(email=None):
    return User.objects.create_superuser(
        email=email or f"super{next(_numbers)}@zchpc.test", password="Str0ng-Passw0rd"
    )


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def new_user_body():
    return {"email": f"created{next(_numbers)}@zchpc.test", "password": "Str0ng-Passw0rd-1"}


def is_read_only_refusal(response):
    return response.status_code == 403 and response.json().get("code") == "READ_ONLY_ACCOUNT"


class TestReadOnlyAccount:
    @pytest.fixture(autouse=True)
    def admin_is_read_only(self, settings):
        settings.READ_ONLY_ACCOUNTS = [ADMIN_EMAIL]

    def test_can_read(self):
        response = client_for(make_superuser(ADMIN_EMAIL)).get(USERS_URL)

        assert response.status_code == 200

    @pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
    def test_every_write_is_refused(self, method):
        admin = make_superuser(ADMIN_EMAIL)
        url = USERS_URL if method == "post" else f"{USERS_URL}{admin.pk}/"

        response = getattr(client_for(admin), method)(url, new_user_body(), format="json")

        assert is_read_only_refusal(response)

    def test_refused_write_changes_nothing(self):
        body = new_user_body()

        client_for(make_superuser(ADMIN_EMAIL)).post(USERS_URL, body, format="json")

        assert not User.objects.filter(email=body["email"]).exists()

    def test_email_matches_case_insensitively(self):
        admin = make_superuser(ADMIN_EMAIL.upper())

        response = client_for(admin).post(USERS_URL, new_user_body(), format="json")

        assert is_read_only_refusal(response)

    def test_can_log_in_refresh_and_log_out(self):
        make_superuser(ADMIN_EMAIL)
        login = APIClient().post(
            "/api/v2/auth/token/",
            {"email": ADMIN_EMAIL, "password": "Str0ng-Passw0rd"},
            format="json",
        )
        assert login.status_code == 200
        tokens = login.json()
        refresh = tokens.get("refresh") or tokens.get("data", {}).get("refresh")

        refreshed = APIClient().post(
            "/api/v2/auth/token/refresh/", {"refresh": refresh}, format="json"
        )
        assert refreshed.status_code == 200

        admin = User.objects.get(email=ADMIN_EMAIL)
        logout = client_for(admin).post("/api/v2/auth/logout/", {"refresh": refresh}, format="json")
        assert logout.status_code == 200

    def test_can_change_own_password(self):
        admin = make_superuser(ADMIN_EMAIL)

        response = client_for(admin).post(
            "/api/v2/auth/password/change/",
            {
                "old_password": "Str0ng-Passw0rd",
                "new_password": "An0ther-Str0ng-Pass",
                "confirm_password": "An0ther-Str0ng-Pass",
            },
            format="json",
        )

        assert not is_read_only_refusal(response)

    def test_django_admin_write_is_refused(self):
        client = Client()
        client.force_login(make_superuser(ADMIN_EMAIL))

        response = client.post("/admin/identity/customuser/add/", new_user_body())

        assert is_read_only_refusal(response)

    def test_other_accounts_are_unaffected(self):
        response = client_for(make_superuser()).post(USERS_URL, new_user_body(), format="json")

        assert not is_read_only_refusal(response)


def test_no_account_is_read_only_by_default(settings):
    settings.READ_ONLY_ACCOUNTS = []
    response = client_for(make_superuser(ADMIN_EMAIL)).post(USERS_URL, new_user_body(), format="json")

    assert not is_read_only_refusal(response)


def test_setting_reads_comma_separated_emails(monkeypatch):
    from erp_root.settings import emails_from_env

    monkeypatch.setenv("READ_ONLY_ACCOUNTS", " Admin@ZCHPC.ac.zw , ,other@zchpc.test")
    assert emails_from_env("READ_ONLY_ACCOUNTS") == ["admin@zchpc.ac.zw", "other@zchpc.test"]

    monkeypatch.delenv("READ_ONLY_ACCOUNTS")
    assert emails_from_env("READ_ONLY_ACCOUNTS") == []
