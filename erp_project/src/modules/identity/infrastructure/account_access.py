"""
Whether an account may authenticate and operate (AUD-02).

The single runtime rule tying a login to the employment lifecycle of the
employee behind it. Every place that lets an identity in asks it, so none of
them decides on CustomUser.is_active alone:

- password login, main and portal (AuthService.authenticate)
- bearer tokens on every request (EmployeeLifecycleJWTAuthentication)
- token refresh (SIMPLE_JWT USER_AUTHENTICATION_RULE)
- Django admin login, and every request on a Django session (EmailBackend)

Lifecycle transitions keep the login switch and the employment state
together (modules.hr EmployeeLifecycleService); this rule is what makes a
disagreement between them - older data, or a write that bypassed the
service - fail closed instead of granting access.
"""

from modules.hr.domain.value_objects import EmployeeLifecycleStatus


def employment_allows_access(user) -> bool:
    """
    False when the login belongs to an employee who is not ACTIVE.

    A login with no employee record (e.g. a bootstrap superuser) has no
    employment lifecycle and is governed by its own is_active flag alone.
    """
    # Reverse one-to-one: Django raises an AttributeError subclass when absent.
    employee = getattr(user, "employee_profile", None)
    if employee is None:
        return True
    return employee.lifecycle_status == EmployeeLifecycleStatus.ACTIVE.value


def account_may_authenticate(user) -> bool:
    """The login is enabled and its employee, if any, is in active employment."""
    return user is not None and bool(user.is_active) and employment_allows_access(user)
