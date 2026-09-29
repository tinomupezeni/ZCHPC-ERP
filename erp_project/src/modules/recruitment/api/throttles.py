"""
Rate limits for the anonymous careers endpoints.

Each is a UserRateThrottle keyed per scope: an authenticated caller is counted
by user, everyone else by client address - so signing in never lifts the
limit. Rates live in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]. The portal's
public careers routes use these same classes, so both paths share one budget.
"""

from rest_framework.throttling import UserRateThrottle


class RecruitmentApplyThrottle(UserRateThrottle):
    scope = "recruitment_apply"


class RecruitmentCheckThrottle(UserRateThrottle):
    scope = "recruitment_check"


class RecruitmentStatusThrottle(UserRateThrottle):
    scope = "recruitment_status"
