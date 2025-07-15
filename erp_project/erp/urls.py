from django.urls import path, include
from . import views
from .view.payroll_view import *
from rest_framework.routers import DefaultRouter
from .view import hr_view, payroll_view

router = DefaultRouter()
router.register(r'zig-rates', ZiGRateToUSDViewSet)
router.register(r'nssa-caps', NSSACapViewSet)
router.register(r'pension-funds', PensionFundViewSet)
router.register(r'employee-deductables', EmployeeDeductablesViewSet)
router.register(r'tax-brackets', TaxBracketViewSet)
router.register(r'payroll-periods', PayrollPeriodViewSet) # New entry

router.register(r'allowance-types', AllowanceTypeViewSet)
router.register(r'deduction-types', DeductionTypeViewSet)



urlpatterns = [
    # system
    path('', include(router.urls)),

    path('register/user/', views.register_user, name='login'),
    path('all/users/', views.get_all_user, name='get_all_users'),
    path('delete/user/<str:id>/', views.delete_user, name='delete_user'),
    path('get/user/<str:id>/', views.get_user, name='delete_user'),
    path('update/user/<str:id>/', views.get_user, name='delete_user'),
    
    # hr module
    path('register/employee/', hr_view.register_employee, name='register_employee'),
    path('all/employees/', hr_view.get_all_employees, name='get_all_users'),
    
    # payroll module
    path('all/payslips/', payroll_view.payroll_list, name='payslip_list'),
    # path('delete/payslip/', payroll_view.delete_employee_slip, name='delete_employee_slip'),
    path('delete/payslip/', payroll_view.DeletePayrollSlipView.as_view(), name='delete_payslip'),

    # urls.py
    path('update-employee-salary/<str:employee_id>/', UpdateEmployeeSalaryView.as_view())

]
