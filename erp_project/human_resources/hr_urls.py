from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .hr_views import PayrollViewSet, EmployeeViewSet, PAYEReportViewSet, NSSAReportViewSet, AllowanceReportViewSet
from .views.address_views import AddressViewSet
from .views.hr_dashboard_view import HrDashboardView 
from .views.training_views import (
    TrainingProgramViewSet,
    TrainingSessionViewSet,
    TrainingEnrollmentViewSet,
    TrainingCertificationViewSet
)
from .views.attendence_views import AttendanceViewSet
from .views.department_views import DepartmentListCreateView, DepartmentDetailView
from .views.org_views import PositionViewSet, DeductionTypeViewSet
from .views.recruitment_views import JobViewSet, JobApplicationViewSet
from .views.report_views import LeaveBalanceReportViewSet, PayrollReportViewSet

router = DefaultRouter()
router.register(r'payrolls', PayrollViewSet, basename='payroll')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'paye', PAYEReportViewSet, basename='paye')
router.register(r'nssa', NSSAReportViewSet, basename='nssa')
router.register(r'allowances', AllowanceReportViewSet, basename='allowances')
router.register(r'deductions', DeductionTypeViewSet, basename='deductions')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'training-programs', TrainingProgramViewSet, basename='training-program')
router.register(r'training-sessions', TrainingSessionViewSet, basename='training-session')
router.register(r'training-enrollments', TrainingEnrollmentViewSet, basename='training-enrollment')
router.register(r'certifications', TrainingCertificationViewSet, basename='certification')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', JobApplicationViewSet, basename='application')
router.register(r'reports/leave-balances', LeaveBalanceReportViewSet, basename='report-leave-balance')

urlpatterns = router.urls

urlpatterns = [
    path('dashboard/', HrDashboardView.as_view(), name='hr-dashboard'),
    path('departments/', DepartmentListCreateView.as_view(), name='department-list-create'),
    path('departments/<int:dept_id>/', DepartmentDetailView.as_view(), name='department-detail'),
    path('reports/paye/', PayrollReportViewSet.as_view({'get': 'paye'}), name='report-paye'),
    path('reports/nssa/', PayrollReportViewSet.as_view({'get': 'nssa'}), name='report-nssa'),
    path('reports/basic-salary/', PayrollReportViewSet.as_view({'get': 'list'}), name='report-basic-salary'),

    path('', include(router.urls)),
]
