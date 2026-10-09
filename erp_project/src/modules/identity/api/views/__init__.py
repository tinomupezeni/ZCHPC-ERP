"""
Identity module API views.
"""

from modules.identity.api.views.admin_views import AdminDashboardView
from modules.identity.api.views.auth_views import AuditLogListView, LoginView
from modules.identity.api.views.system_module_views import SystemModuleViewSet
from modules.identity.api.views.user_views import (
    ChangePasswordView,
    CurrentUserAccessView,
    CurrentUserView,
    UnlockUserView,
    UserDetailView,
    UserListCreateView,
)

__all__ = [
    "AdminDashboardView",
    "LoginView",
    "AuditLogListView",
    "UserListCreateView",
    "UserDetailView",
    "CurrentUserView",
    "CurrentUserAccessView",
    "ChangePasswordView",
    "UnlockUserView",
    "SystemModuleViewSet",
]
