"""
Leave API URL configuration.
"""

from django.urls import path

from modules.leave.api.views import (
    InitializeBalancesView,
    LeaveBalanceAdminView,
    LeaveBalanceAdjustView,
    LeaveBalanceDetailView,
    LeaveBalanceListView,
    LeaveRequestCancelView,
    LeaveRequestDetailView,
    LeaveRequestListView,
    LeaveRequestReviewView,
    LeaveRequestSummaryView,
    LeaveTypeDetailView,
    LeaveTypeListView,
    PendingLeaveRequestsView,
)

app_name = "leave"

urlpatterns = [
    # Leave Types
    path("types/", LeaveTypeListView.as_view(), name="leave-type-list"),
    path("types/<int:leave_type_id>/", LeaveTypeDetailView.as_view(), name="leave-type-detail"),

    # Leave Balances
    path("balances/", LeaveBalanceListView.as_view(), name="leave-balance-list"),
    path("balances/<int:balance_id>/", LeaveBalanceDetailView.as_view(), name="leave-balance-detail"),
    path("balances/<int:balance_id>/adjust/", LeaveBalanceAdjustView.as_view(), name="leave-balance-adjust"),
    path("balances/admin/", LeaveBalanceAdminView.as_view(), name="leave-balance-admin"),
    path("balances/initialize/<int:employee_id>/", InitializeBalancesView.as_view(), name="leave-balance-initialize"),

    # Leave Requests
    path("requests/", LeaveRequestListView.as_view(), name="leave-request-list"),
    path("requests/<int:request_id>/", LeaveRequestDetailView.as_view(), name="leave-request-detail"),
    path("requests/<int:request_id>/cancel/", LeaveRequestCancelView.as_view(), name="leave-request-cancel"),
    path("requests/<int:request_id>/review/", LeaveRequestReviewView.as_view(), name="leave-request-review"),
    path("requests/pending/", PendingLeaveRequestsView.as_view(), name="leave-request-pending"),
    path("requests/summary/", LeaveRequestSummaryView.as_view(), name="leave-request-summary"),
]
