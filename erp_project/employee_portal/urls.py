from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.auth_views import (
    EmployeeLoginView,
    EmployeeTokenRefreshView,
    EmployeeLogoutView,
    EmployeeMeView,
)
from .views.dashboard_views import (
    DashboardView,
    NotificationViewSet,
)
from .views.profile_views import (
    EmployeeProfileView,
    ProfilePhotoView,
)
from .views.attendance_views import (
    ClockInOutView,
    AttendanceStatusView,
    AttendanceHistoryView,
    AttendanceSummaryView,
    QRTokenView,
    QRClockInView,
)
from .views.leave_views import (
    LeaveTypeListView,
    LeaveBalanceView,
    LeaveRequestViewSet,
    LeaveRequestCancelView,
)
from .views.payslip_views import (
    PayslipListView,
    PayslipDetailView,
    PayslipYearSummaryView,
    PayslipDownloadView,
)
from .views.expense_views import (
    ExpenseCategoryListView,
    ExpenseClaimViewSet,
)
from .views.ticket_views import (
    TicketViewSet,
)
from .views.document_views import (
    DocumentCategoryListView,
    DocumentViewSet,
)
from .views.public_views import (
    PublicJobListView,
    PublicJobDetailView,
    CheckApplicationView,
    SubmitApplicationView,
    ApplicationStatusView,
)

app_name = 'employee_portal'

# Router for viewsets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'leave/requests', LeaveRequestViewSet, basename='leave-request')
router.register(r'expenses', ExpenseClaimViewSet, basename='expense')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    # Public endpoints (no authentication required)
    path('public/jobs/', PublicJobListView.as_view(), name='public-jobs'),
    path('public/jobs/<int:pk>/', PublicJobDetailView.as_view(), name='public-job-detail'),
    path('public/jobs/check-application/', CheckApplicationView.as_view(), name='check-application'),
    path('public/jobs/apply/', SubmitApplicationView.as_view(), name='submit-application'),
    path('public/applications/status/', ApplicationStatusView.as_view(), name='application-status'),

    # Authentication endpoints
    path('auth/login/', EmployeeLoginView.as_view(), name='login'),
    path('auth/refresh/', EmployeeTokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', EmployeeLogoutView.as_view(), name='logout'),
    path('auth/me/', EmployeeMeView.as_view(), name='me'),

    # Dashboard endpoints
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Profile endpoints
    path('profile/', EmployeeProfileView.as_view(), name='profile'),
    path('profile/photo/', ProfilePhotoView.as_view(), name='profile-photo'),

    # Attendance endpoints
    path('attendance/clock/', ClockInOutView.as_view(), name='attendance-clock'),
    path('attendance/status/', AttendanceStatusView.as_view(), name='attendance-status'),
    path('attendance/history/', AttendanceHistoryView.as_view(), name='attendance-history'),
    path('attendance/summary/', AttendanceSummaryView.as_view(), name='attendance-summary'),
    path('attendance/qr/token/', QRTokenView.as_view(), name='qr-token'),
    path('attendance/qr/clock-in/', QRClockInView.as_view(), name='qr-clock-in'),

    # Leave endpoints
    path('leave/types/', LeaveTypeListView.as_view(), name='leave-types'),
    path('leave/balances/', LeaveBalanceView.as_view(), name='leave-balances'),
    path('leave/requests/<int:pk>/cancel/', LeaveRequestCancelView.as_view(), name='leave-request-cancel'),

    # Payslip endpoints
    path('payslips/', PayslipListView.as_view(), name='payslip-list'),
    path('payslips/summary/', PayslipYearSummaryView.as_view(), name='payslip-summary'),
    path('payslips/<int:pk>/', PayslipDetailView.as_view(), name='payslip-detail'),
    path('payslips/<int:pk>/download/', PayslipDownloadView.as_view(), name='payslip-download'),

    # Expense endpoints
    path('expenses/categories/', ExpenseCategoryListView.as_view(), name='expense-categories'),

    # Document endpoints
    path('documents/categories/', DocumentCategoryListView.as_view(), name='document-categories'),

    # Router URLs (notifications, leave requests, expenses, tickets, documents)
    path('', include(router.urls)),
]
