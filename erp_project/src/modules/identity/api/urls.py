"""
Identity module URL configuration.

These URLs are mounted under /api/v2/auth/
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from modules.identity.api.views import (
    AuditLogListView,
    CurrentUserView,
    LoginView,
    UnlockUserView,
    UserDetailView,
    UserListCreateView,
)

app_name = "identity"

urlpatterns = [
    # Authentication
    path("token/", LoginView.as_view(), name="token_obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Users
    path("users/", UserListCreateView.as_view(), name="user_list"),
    path("users/me/", CurrentUserView.as_view(), name="user_me"),
    path("users/<str:user_id>/", UserDetailView.as_view(), name="user_detail"),
    path("users/<str:user_id>/unlock/", UnlockUserView.as_view(), name="user_unlock"),

    # Audit Logs
    path("logs/", AuditLogListView.as_view(), name="audit_logs"),
]
