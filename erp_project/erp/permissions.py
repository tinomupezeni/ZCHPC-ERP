ROLE_PERMISSIONS = {
    "ADMIN": ["*"],  # Full access
    "HR": [
        "employees.view",
        "employees.add",
        "employees.update",
        "payroll.view"
    ],
    "ACCOUNTANT": [
        "payroll.view",
        "payroll.update",
        "invoices.view"
    ],
    "PROCUREMENT": [
        "procurement.view",
        "procurement.add",
        "procurement.update"
    ],
    "SALES": [
        "sales.view",
        "sales.add",
        "sales.update"
    ],
    "MANAGER": [
        "reports.view",
        "employees.view",
        "projects.view"
    ],
    "STAFF": [
        "self.view",
        "self.update"
    ],
    "INTERN": [
        "self.view"
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
