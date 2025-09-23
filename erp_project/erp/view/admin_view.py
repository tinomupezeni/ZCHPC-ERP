
from erp.dependencies import *

class DashboardDataView(APIView):
    def get(self, request, *args, **kwargs):
        # 1. Total Employees
        total_employees = Employees.objects.count()

        # 2. Total Attendees Today (You'll need an attendance model for this)
        # For now, let's assume all active employees attended.
        active_employees = Employees.objects.filter(isActive=True).count()
        
        # 3. Employee Distribution by Department
        employee_distribution = Employees.objects.values('department').annotate(employees=Count('id'))
        
        # 4. Payroll Distribution by Department (by total salary this month)
        # This requires calculating total salaries per department for the current month.
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        # Get all payroll entries for the current month
        monthly_payroll_data = Payroll.objects.filter(
            period__month=current_month,
            period__year=current_year
        )
        
        # Aggregate by department
        payroll_distribution = monthly_payroll_data.values(
            'employee__department'
        ).annotate(
            total_usd=Sum('net_salary_usd'),
            total_zig=Sum('net_salary_zig')
        )
        
        # 5. Recent Activities (assuming you have a log/activity model)
        # For this example, we'll use a placeholder.
        recent_activities = [] 
        
        # 6. Tasks Due (assuming you have a tasks model)
        # For this example, we'll use a placeholder.
        tasks_due = [] 

        data = {
            'metrics': {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'total_attendees': active_employees, # Placeholder until attendance is implemented
            },
            'charts': {
                'employee_distribution': list(employee_distribution),
                'payroll_distribution': list(payroll_distribution),
            },
            'lists': {
                'recent_activities': recent_activities,
                'tasks_due': tasks_due,
            }
        }
        return Response(data)