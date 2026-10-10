"""
Logout: revoke the caller's own refresh token (B3, INT-01).
"""

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken


def revoke_own_refresh_token(user, raw_token) -> None:
    """
    Blacklist ``raw_token`` if it is a valid refresh token belonging to
    ``user``. A missing, malformed, expired or already-blacklisted token has
    nothing left to revoke; a token that belongs to another user is left
    alone. Never raises, so logout can always succeed.
    """
    if not raw_token:
        return
    try:
        token = RefreshToken(raw_token)
    except TokenError:
        return
    if str(token.get(jwt_settings.USER_ID_CLAIM)) == str(user.pk):
        token.blacklist()
