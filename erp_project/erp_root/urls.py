"""
ZCHPC ERP URL Configuration

All API endpoints are now available at /api/v2/*
The legacy v1 API endpoints have been removed.

For API documentation, see /api/v2/docs/ (OpenAPI/Swagger)

For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from modules.identity.api.views import AdminDashboardView


def health_check(request):
    """Health check endpoint for Docker/Kubernetes."""
    return JsonResponse({'status': 'healthy', 'service': 'zchpc-erp'})


urlpatterns = [
    # =========================================================================
    # Health Check (for Docker/load balancers)
    # =========================================================================
    path('api/v2/health/', health_check, name='health_check'),

    # =========================================================================
    # Django Admin
    # =========================================================================
    path('admin/', admin.site.urls),

    # =========================================================================
    # Admin Dashboard API
    # =========================================================================
    path('api/v2/admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),

    # =========================================================================
    # API v2 - Modular Architecture
    # =========================================================================
    # All API endpoints follow clean architecture principles with clear
    # separation between modules.
    # =========================================================================
    path('api/v2/auth/', include('modules.identity.api.urls', namespace='identity')),
    path('api/v2/hr/', include('modules.hr.api.urls', namespace='hr')),
    path('api/v2/attendance/', include('modules.attendance.api.urls', namespace='attendance')),
    path('api/v2/leave/', include('modules.leave.api.urls', namespace='leave')),
    path('api/v2/recruitment/', include('modules.recruitment.api.urls', namespace='recruitment')),
    path('api/v2/payroll/', include('modules.payroll.api.urls', namespace='payroll')),
    path('api/v2/accounts/', include('modules.accounts.api.urls', namespace='accounts_v2')),
    path('api/v2/procurement/', include('modules.procurement.api.urls', namespace='procurement_v2')),
    path('api/v2/portal/', include('modules.portal.api.urls', namespace='portal_v2')),

    # =========================================================================
    # Development Tools
    # =========================================================================
    path("__reload__/", include("django_browser_reload.urls")),
]
