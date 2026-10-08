"""
Which existing login a new employee record is attached to (AUD-02 F7/F9).

A new employee whose email matches an existing login is attached to that
login. EmployeeService resolves it to authorize the attachment before
anything is created (F7); the post_save signal resolves it for records made
any other way. Both use this one rule, so they cannot pick different logins:

- emails are one identity whatever their letter case, as identity itself
  treats them (sign-in and the duplicate check match case-insensitively);
- a login that already belongs to an employee is not attachable: the email
  is that employee's (DUPLICATE_EMAIL);
- logins differing only by case are ambiguous, and nothing is attached.

Who may attach a login is not decided here; that is EmployeeService's
authorization.
"""

from shared.domain.exceptions import ValidationError


def attachable_login(email: str | None):
    """
    The existing login a new employee with this email is attached to, or
    None if no login has it.

    Raises:
        ValidationError: DUPLICATE_EMAIL if the matching login already
            belongs to an employee; AMBIGUOUS_LOGIN_EMAIL if more than one
            login matches
    """
    if not email or not email.strip():
        return None

    from modules.hr.infrastructure.persistence.models import Employees
    from modules.identity.infrastructure.persistence.models import CustomUser

    matches = list(CustomUser.objects.filter(email__iexact=email.strip())[:2])
    if not matches:
        return None
    if len(matches) > 1:
        raise ValidationError(
            message=f"More than one account matches {email}; none is attached",
            code="AMBIGUOUS_LOGIN_EMAIL",
        )
    login = matches[0]
    if Employees.objects.filter(user_id=login.pk).exists():
        raise ValidationError(
            message=f"Email {email} belongs to another employee's account",
            code="DUPLICATE_EMAIL",
        )
    return login
