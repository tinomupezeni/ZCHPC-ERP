"""
Payroll API URL configuration.
"""

from django.urls import path

from modules.payroll.api.views import (
    # Tax brackets
    TaxBracketListView,
    TaxBracketDetailView,
    # Exchange rates
    ExchangeRateListView,
    ExchangeRateDetailView,
    LatestExchangeRateView,
    # Payslips
    PayslipListView,
    PayslipDetailView,
    PayslipApproveView,
    # Payroll
    PayrollSummaryView,
    # Types
    AllowanceTypeListView,
    DeductionTypeListView,
)

app_name = "payroll"

urlpatterns = [
    # Tax brackets
    path(
        "tax-brackets/",
        TaxBracketListView.as_view(),
        name="tax-bracket-list"
    ),
    path(
        "tax-brackets/<int:bracket_id>/",
        TaxBracketDetailView.as_view(),
        name="tax-bracket-detail"
    ),

    # Exchange rates
    path(
        "rates/",
        ExchangeRateListView.as_view(),
        name="exchange-rate-list"
    ),
    path(
        "rates/<int:rate_id>/",
        ExchangeRateDetailView.as_view(),
        name="exchange-rate-detail"
    ),
    path(
        "rates/latest/",
        LatestExchangeRateView.as_view(),
        name="exchange-rate-latest"
    ),

    # Payslips
    path(
        "payslips/",
        PayslipListView.as_view(),
        name="payslip-list"
    ),
    path(
        "payslips/<int:payslip_id>/",
        PayslipDetailView.as_view(),
        name="payslip-detail"
    ),
    path(
        "payslips/<int:payslip_id>/approve/",
        PayslipApproveView.as_view(),
        name="payslip-approve"
    ),

    # Payroll summary
    path(
        "summary/",
        PayrollSummaryView.as_view(),
        name="payroll-summary"
    ),

    # Allowance & Deduction types
    path(
        "allowance-types/",
        AllowanceTypeListView.as_view(),
        name="allowance-type-list"
    ),
    path(
        "deduction-types/",
        DeductionTypeListView.as_view(),
        name="deduction-type-list"
    ),
]

from modules.payroll.api.views import PayrollProfileDetailView, StatutoryProfileDetailView, EmployeeBankAccountListView

urlpatterns += [
    path('profiles/<uuid:employee_id>/', PayrollProfileDetailView.as_view(), name='payroll-profile-detail'),
    path('statutory/<uuid:employee_id>/', StatutoryProfileDetailView.as_view(), name='statutory-profile-detail'),
    path('bank-accounts/<uuid:employee_id>/', EmployeeBankAccountListView.as_view(), name='employee-bank-accounts'),
]
