"""erp_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from human_resources.views.org_views import AllowanceTypeViewSet, DeductionTypeViewSet
from payroll.payroll_views import TaxBracketViewSet, PayrollPeriodViewSet

# Router for root-level API endpoints
api_router = DefaultRouter()
api_router.register(r'allowance-types', AllowanceTypeViewSet, basename='allowance-type')
api_router.register(r'deduction-types', DeductionTypeViewSet, basename='deduction-type')
api_router.register(r'tax-brackets', TaxBracketViewSet, basename='tax-bracket')
api_router.register(r'payroll-periods', PayrollPeriodViewSet, basename='payroll-period')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/payroll/', include('payroll.payroll_urls')),
    path('api/hr/', include('human_resources.hr_urls')),
    path('api/procurement/', include('procurement.urls')),
    path('api/admin/', include('administration.urls')),
    path('api/portal/', include('employee_portal.urls')),  # Employee portal API
    path('api/', include(api_router.urls)),  # Root-level API routes
    path("__reload__/", include("django_browser_reload.urls")),
]
