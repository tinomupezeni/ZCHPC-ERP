"""
Role-based permissions configuration for the Identity module.

Permissions use a pattern matching system where:
- "*" means full access
- "module.*" means access to all endpoints in that module
- "module.endpoint" means access to a specific endpoint
"""
from rest_framework.permissions import BasePermission

# HR role permissions
_HR_PERMISSIONS = [
    "hr.*",
    "attendance.*",
    "leave.*",
    "recruitment.*",
    "payroll.*",
    "identity.*",
    "portal.*",
]

# Employee portal permissions - all employees can access their own portal
_EMPLOYEE_PORTAL_PERMISSIONS = [
    "portal.*",
    "identity.*",
]

ROLE_PERMISSIONS = {
    "ADMIN": ["*"],
    "SYSTEM_ADMINISTRATOR": ["*"],
    "HR": _HR_PERMISSIONS,
    "HUMAN_RESOURCES": _HR_PERMISSIONS,
    "ACCOUNTANT": [
        "payroll.*",
        "accounts.*",
        "identity.*",
        "portal.*",
    ],
    "PROCUREMENT": [
        "procurement.*",
        "identity.*",
        "portal.*",
    ],
    "PROCUREMENT_OFFICER": [
        "procurement.*",
        "identity.*",
        "portal.*",
    ],
    "SALES": [
        "sales.*",
        "identity.*",
        "portal.*",
    ],
    "SALES_REPRESENTATIVE": [
        "sales.*",
        "identity.*",
        "portal.*",
    ],
    "MANAGER": [
        "hr.*",
        "attendance.*",
        "leave.*",
        "payroll.*",
        "reports.*",
        "identity.*",
        "portal.*",
    ],
    "DEPARTMENT_MANAGER": [
        "hr.*",
        "attendance.*",
        "leave.*",
        "payroll.*",
        "reports.*",
        "identity.*",
        "portal.*",
    ],
    "STAFF": [
        "identity.*",
        "self.*",
        "portal.*",
    ],
    "REGULAR_STAFF": [
        "identity.*",
        "self.*",
        "portal.*",
    ],
    "INTERN": [
        "identity.*",
        "self.*",
        "portal.*",
    ],
}


class RolePermission(BasePermission):
    """Permission class that checks if user has one of the allowed roles."""

    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Get role from employee profile
        # Use try-except because OneToOne reverse relations raise DoesNotExist
        try:
            employee = request.user.employee_profile
            if employee:
                role_obj = getattr(employee, 'role', None)
                user_role = getattr(role_obj, 'name', 'STAFF') if role_obj else 'STAFF'
            else:
                user_role = 'STAFF'
        except Exception:
            # No employee profile - check if superuser
            if request.user.is_superuser or request.user.is_staff:
                user_role = 'ADMIN'
            else:
                user_role = 'STAFF'

        return user_role.upper() in [r.upper() for r in self.allowed_roles]
