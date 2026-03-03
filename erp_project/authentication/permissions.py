# HR role permissions - used by both "HR" and "HUMAN_RESOURCES" role names
_HR_PERMISSIONS = [
    "hr.*",  # All HR endpoints
    "human_resources.*",  # All human_resources app endpoints
    "payroll.*",  # All payroll endpoints
    "employees.*",
    "authentication.*",  # Auth endpoints
    "administration.*",  # Dashboard access
    "employee_portal.*",  # Employee portal access
]

# Employee portal permissions - all employees can access their own portal
_EMPLOYEE_PORTAL_PERMISSIONS = [
    "employee_portal.*",  # Employee portal endpoints
    "authentication.*",
]

ROLE_PERMISSIONS = {
    "ADMIN": ["*"],  # Full access
    "SYSTEM_ADMINISTRATOR": ["*"],  # Alias for ADMIN
    "HR": _HR_PERMISSIONS,
    "HUMAN_RESOURCES": _HR_PERMISSIONS,  # Alias for HR
    "ACCOUNTANT": [
        "payroll.*",  # All payroll endpoints
        "accounts.*",  # All accounts endpoints
        "authentication.*",
        "administration.*",  # Dashboard access
        "employee_portal.*",  # Employee portal access
    ],
    "PROCUREMENT": [
        "procurement.*",  # All procurement endpoints
        "authentication.*",
        "administration.*",  # Dashboard access
        "employee_portal.*",  # Employee portal access
    ],
    "PROCUREMENT_OFFICER": [  # Alias
        "procurement.*",
        "authentication.*",
        "administration.*",
        "employee_portal.*",
    ],
    "SALES": [
        "sales.*",
        "authentication.*",
        "administration.*",  # Dashboard access
        "employee_portal.*",  # Employee portal access
    ],
    "SALES_REPRESENTATIVE": [  # Alias
        "sales.*",
        "authentication.*",
        "administration.*",
        "employee_portal.*",
    ],
    "MANAGER": [
        "hr.*",
        "payroll.*",
        "reports.*",
        "employees.*",
        "authentication.*",
        "administration.*",  # Dashboard access
        "employee_portal.*",  # Employee portal access
    ],
    "DEPARTMENT_MANAGER": [  # Alias
        "hr.*",
        "payroll.*",
        "reports.*",
        "employees.*",
        "authentication.*",
        "administration.*",
        "employee_portal.*",
    ],
    "STAFF": [
        "authentication.*",
        "self.*",
        "administration.*",  # Allow dashboard access
        "employee_portal.*",  # Employee portal access
    ],
    "REGULAR_STAFF": [  # Alias
        "authentication.*",
        "self.*",
        "administration.*",
        "employee_portal.*",
    ],
    "INTERN": [
        "authentication.*",
        "self.*",
        "employee_portal.*",  # Employee portal access
    ],
}

from rest_framework.permissions import BasePermission

class RolePermission(BasePermission):
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )
