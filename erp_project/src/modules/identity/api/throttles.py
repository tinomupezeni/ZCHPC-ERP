"""
Rate limit for the login endpoints (B10).

One budget per client address, shared by the main login
(/api/v2/auth/token/) and the portal login (/api/v2/portal/auth/login/), so
switching endpoints never doubles the attempts. Every attempt counts, whether
it succeeds or not, and sending a token does not lift the limit. The rate
lives in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"]; the client
address comes from DRF's get_ident, which honours NUM_PROXIES.

This sits in front of the per-account lockout (5 failed passwords), which
stops guessing one account; the throttle stops one address trying many.
"""

from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
