from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .hr_views import PayrollViewSet, EmployeeViewSet, PAYEReportViewSet, NSSAReportViewSet, AllowanceReportViewSet, DeductionReportViewSet


router = DefaultRouter()
router.register(r'payrolls', PayrollViewSet, basename='payroll')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'paye', PAYEReportViewSet, basename='paye')
router.register(r'nssa', NSSAReportViewSet, basename='nssa')
router.register(r'allowances', AllowanceReportViewSet, basename='allowances')
router.register(r'deductions', DeductionReportViewSet, basename='deductions')


urlpatterns = router.urls

