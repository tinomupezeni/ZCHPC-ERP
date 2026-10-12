"""
Django settings for the automated test suite only.

Selected by pytest (pytest.ini / pyproject.toml DJANGO_SETTINGS_MODULE).
Nothing else points here: manage.py, wsgi.py, asgi.py and the desktop entry
point all default to erp_root.settings, which is unchanged.

Identical to erp_root.settings except for one thing: passwords are hashed
with PBKDF2-SHA256 at a much lower work factor. The production hasher is
Django's PBKDF2PasswordHasher at 1,000,000+ iterations - about 0.4 s per
hash or check - and measurement showed that hashing was ~90% of test
runtime. The algorithm, the encoded format ("pbkdf2_sha256$..."), password
validation and verification (including rejecting a wrong password) are all
unchanged; only the iteration count differs. PBKDF2 reads the iteration count
from each stored hash, so hashes made at either work factor verify under
either setting.

tests/unit/test_password_hasher_settings.py checks that production still
uses the full-strength hasher and that this module differs from production
in nothing but PASSWORD_HASHERS.

USE_SQLITE and every other environment switch behave exactly as in
erp_root.settings, which this module imports in full.
"""

from django.contrib.auth.hashers import PBKDF2PasswordHasher

from erp_root.settings import *  # noqa: F401,F403


class FastPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """PBKDF2-SHA256 at a test-only work factor; same algorithm and format."""

    iterations = 1_000


PASSWORD_HASHERS = ["erp_root.settings_test.FastPBKDF2PasswordHasher"]
