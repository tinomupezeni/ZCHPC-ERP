from django.urls import path, include

from .view.audit_view import AuditLogListView

from .view.hr_dashboard_view import HrDashboardView
from . import views
from .view.payroll_view import *
from rest_framework.routers import DefaultRouter
from .view import hr_view, payroll_view
from .view.system_user_view import *
from .view.registeruser import *
from .view.admin_view import *
from .view.department_view import DepartmentViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# Correct import path for the jobs list/create view
from .view.jobs_view import JobListCreate, JobDetail, JobToggleStatus
from .view.auth_view import CustomTokenObtainPairView

router = DefaultRouter()
router.register(r'zig-rates', ZiGRateToUSDViewSet)
router.register(r'nssa-caps', NSSACapViewSet)
router.register(r'pension-funds', PensionFundViewSet)
router.register(r'employee-deductables', EmployeeDeductablesViewSet)
router.register(r'tax-brackets', TaxBracketViewSet)
router.register(r'payroll-periods', PayrollPeriodViewSet)

router.register(r'allowance-types', AllowanceTypeViewSet)
router.register(r'deduction-types', DeductionTypeViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'users', CustomUserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),

    path('register/user/', views.register_user, name='login'),
    path('all/users/', views.get_all_user, name='get_all_users'),
    path('delete/user/<str:id>/', views.delete_user, name='delete_user'),
    path('get/user/<str:id>/', views.get_user, name='get_user'),
    path('update/user/<str:id>/', views.get_user, name='update_user'),

    # Use default simplejwt views — no custom serializer needed
    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('user-details/', UserDetailsView.as_view(), name='user_details'),

    # HR Module URLs
    path('register/employee/', hr_view.register_employee, name='register_employee'),
    path('all/employees/', hr_view.get_all_employees, name='get_all_employees'),
    path('register/training/program/', hr_view.training_program_list, name='register_training_program'),
    path('all/training/programs/', hr_view.training_program_list, name='get_all_training_programs'),
    path('update/training/program/<int:pk>/', hr_view.training_program_detail, name='update_training_program'),
    path('delete/training/program/<int:pk>/', hr_view.training_program_detail, name='delete_training_program'),

    # Training Sessions
    path('training/sessions/', hr_view.training_session_list, name='training-session-list'),
    path('training/sessions/<int:pk>/', hr_view.training_session_detail, name='training-session-detail'),

    # Training Enrollments
    path('training/enrollments/', hr_view.training_enrollment_list, name='training-enrollment-list'),
    path('training/enrollments/<int:pk>/', hr_view.training_enrollment_detail, name='training-enrollment-detail'),

    # Training Certifications
    path('training/certifications/', hr_view.certification_list, name='certification-list'),
    path('training/certifications/<int:pk>/', hr_view.certification_detail, name='certification-detail'),
    path('training/certifications/search/', hr_view.certification_search, name='certification-search'),

    # Payroll Module
    path('all/payslips/', payroll_view.payroll_list, name='payslip_list'),
    path('delete/payslip/', payroll_view.DeletePayrollSlipView.as_view(), name='delete_payslip'),

    # Update employee salary
    path('update-employee-salary/<str:employee_id>/', UpdateEmployeeSalaryView.as_view()),
    
    # Admin Dashboard
    path('dashboard-data/', DashboardDataView.as_view(), name='dashboard_data'),

# HR Dashboard-specific URL
    path('hr-dashboard/', HrDashboardView.as_view(), name='hr-dashboard'),
    
    # job detail & status
    path('jobs/<int:pk>/', JobDetail.as_view(), name='job-detail'),
    path('jobs/<int:pk>/toggle_status/', JobToggleStatus.as_view(), name='job-toggle-status'),
    
      # Attendance endpoints (match frontend calls)
    path('all/attendance/', hr_view.attendance_list, name='attendance_list'),
    path('delete/attendance/<int:pk>/', hr_view.attendance_delete, name='attendance_delete'),
    path('upload/attendance/', hr_view.attendance_bulk_upload, name='attendance_bulk_upload'),
    
    # System logs
    path("logs/", AuditLogListView.as_view(), name="audit-log-list"),
    
    # Get the latest ZiG exchange rate

    path("rates/latest/", get_latest_rate, name="latest-rate"),
    path("rates/", get_all_rates, name="all-rates"),
    

]
