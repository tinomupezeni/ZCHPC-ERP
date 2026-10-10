"""
JWT lifetimes come from the environment (AUDIT §1: JWT_* were never read),
so staging can use a short access token for the AUTH-1 expiry test.
"""

from datetime import timedelta

import pytest
from django.core.exceptions import ImproperlyConfigured

from erp_root.settings import token_lifetime_from_env

NAMES = [
    f"JWT_{kind}_TOKEN_LIFETIME_{unit}"
    for kind in ("ACCESS", "REFRESH")
    for unit in ("MINUTES", "DAYS")
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)


def test_unset_gives_the_default():
    assert token_lifetime_from_env("ACCESS", default_days=1) == timedelta(days=1)


def test_empty_counts_as_unset(monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", "")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_LIFETIME_DAYS", " ")
    assert token_lifetime_from_env("ACCESS", default_days=1) == timedelta(days=1)


def test_days(monkeypatch):
    monkeypatch.setenv("JWT_REFRESH_TOKEN_LIFETIME_DAYS", "7")
    assert token_lifetime_from_env("REFRESH", default_days=30) == timedelta(days=7)


def test_minutes_win_over_days(monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_LIFETIME_DAYS", "1")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", "2")
    assert token_lifetime_from_env("ACCESS", default_days=1) == timedelta(minutes=2)


def test_kinds_are_independent(monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", "2")
    assert token_lifetime_from_env("REFRESH", default_days=30) == timedelta(days=30)


@pytest.mark.parametrize("raw", ["abc", "1.5", "0", "-3"])
def test_bad_values_fail_loudly(monkeypatch, raw):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", raw)
    with pytest.raises(ImproperlyConfigured):
        token_lifetime_from_env("ACCESS", default_days=1)
