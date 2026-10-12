"""
The test-only password hasher must stay test-only.

The suite runs under erp_root.settings_test, which lowers the PBKDF2 work
factor for speed. These tests read the production settings module directly
- not django.conf.settings, which is the test configuration here - so they
keep checking what production actually uses.
"""

import importlib
from pathlib import Path

import pytest
from django.conf import global_settings, settings
from django.contrib.auth.hashers import (
    PBKDF2PasswordHasher,
    check_password,
    get_hasher,
    make_password,
)
from django.utils.module_loading import import_string

PRODUCTION_SETTINGS = "erp_root.settings"
TEST_SETTINGS = "erp_root.settings_test"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _production():
    return importlib.import_module(PRODUCTION_SETTINGS)


def _production_hashers():
    return getattr(_production(), "PASSWORD_HASHERS", global_settings.PASSWORD_HASHERS)


def _settings_names(module):
    return {name for name in dir(module) if name.isupper()}


class TestProductionHasher:
    def test_production_uses_djangos_full_strength_pbkdf2(self):
        hasher = import_string(_production_hashers()[0])
        assert hasher is PBKDF2PasswordHasher  # the class itself, not a subclass
        assert hasher.algorithm == "pbkdf2_sha256"
        assert hasher.iterations >= 1_000_000

    def test_production_hashes_verify_and_reject(self):
        hasher = import_string(_production_hashers()[0])()
        encoded = hasher.encode("Correct-Horse-1", hasher.salt())
        assert encoded.startswith(f"pbkdf2_sha256${hasher.iterations}$")
        assert hasher.verify("Correct-Horse-1", encoded)
        assert not hasher.verify("Wrong-Horse-1", encoded)


class TestTestSettingsAreTestOnly:
    def test_the_suite_runs_under_the_test_settings(self):
        assert settings.SETTINGS_MODULE == TEST_SETTINGS

    def test_test_settings_differ_from_production_only_in_the_hasher(self):
        production = _production()
        test = importlib.import_module(TEST_SETTINGS)
        differing = {
            name
            for name in _settings_names(production) | _settings_names(test)
            if getattr(production, name, None) != getattr(test, name, None)
        }
        assert differing == {"PASSWORD_HASHERS"}

    @pytest.mark.parametrize(
        "entry_point",
        ["manage.py", "erp_root/wsgi.py", "erp_root/asgi.py", "desktop_entrypoint.py"],
    )
    def test_entry_points_select_production_settings(self, entry_point):
        source = (PROJECT_ROOT / entry_point).read_text(encoding="utf-8")
        assert f"'DJANGO_SETTINGS_MODULE', '{PRODUCTION_SETTINGS}'" in source
        assert TEST_SETTINGS not in source


class TestTestHasher:
    def test_same_algorithm_lower_work_factor(self):
        hasher = get_hasher()
        assert isinstance(hasher, PBKDF2PasswordHasher)
        assert hasher.algorithm == "pbkdf2_sha256"
        assert hasher.iterations < PBKDF2PasswordHasher.iterations

    def test_verification_still_accepts_and_rejects(self):
        encoded = make_password("Correct-Horse-1")
        assert encoded.startswith("pbkdf2_sha256$")
        assert check_password("Correct-Horse-1", encoded)
        assert not check_password("Wrong-Horse-1", encoded)
        assert not check_password("", encoded)

    def test_a_full_strength_hash_still_verifies_under_test_settings(self):
        """PBKDF2 reads the work factor from the stored hash."""
        production = PBKDF2PasswordHasher()
        encoded = production.encode("Correct-Horse-1", production.salt())
        assert check_password("Correct-Horse-1", encoded)
        assert not check_password("Wrong-Horse-1", encoded)
