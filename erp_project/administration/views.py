from django.utils import timezone
from django.db.models import Count, Sum, F, Value
from rest_framework import status
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

# Import models from all your apps
from human_resources.hr_models import Employees, AttendanceRecord
from payroll.payroll_models import Payroll, PayrollPeriod
from authentication.models import AuditLog

# Import a serializer for your audit logs
from authentication.serializers.audit_serializer import AuditLogSerializer

class AdminDashboardView(APIView):
    """
    A view to return all necessary aggregated data for the main Admin dashboard.
    """
    # Only authenticated admin users can access this
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = timezone.now().date()

        # --- 1. Metrics ---
        total_employees = Employees.objects.filter(is_active=True).count()
        
        # Count employees who have a 'time_in' record for today
        total_attendees = AttendanceRecord.objects.filter(
            date=today, 
            time_in__isnull=False
        ).count()

        # --- 2. Charts ---
        
        # Employees distribution by department
        employee_dist = Employees.objects.filter(is_active=True) \
            .annotate(department_name=Coalesce('department__name', Value('Unassigned'))) \
            .values('department_name') \
            .annotate(department=F('department_name'), employees=Count('id')) \
            .values('department', 'employees') \
            .order_by('-employees')

        # Payroll distribution by department (for the last processed period)
        latest_period = PayrollPeriod.objects.order_by('-end_date').first()
        payroll_dist = []
        if latest_period:
            payroll_dist = Payroll.objects.filter(period=latest_period) \
                .annotate(dept_name=Coalesce('employee__department__name', Value('Unassigned'))) \
                .values('dept_name') \
                .annotate(
                    employee__department=F('dept_name'), # Match frontend key
                    total_usd=Sum('net_salary_usd'),
                    total_zig=Sum('net_salary_zig')
                ) \
                .values('employee__department', 'total_usd', 'total_zig') \
                .order_by('-total_usd')

        # --- 3. Lists ---
        
        # Mock data for "Tasks Due" as seen in your frontend
        # TODO: Replace this with a real query to a 'Task' model later
        tasks_due = [
            {"id": 1, "text": "Approve T. Mupezeni's leave request", "done": False, "module": "hr", "due": "Today"},
            {"id": 2, "text": "Review procurement budget Q4", "done": False, "module": "procurement", "due": "Tomorrow"},
            {"id": 3, "text": "Finalize monthly payroll", "done": True, "module": "payroll", "due": "Yesterday"},
        ]
        
        # Get the 5 most recent activities from the AuditLog
        recent_activities = AuditLog.objects.all().order_by('-timestamp')[:5]
        
        # --- 4. Assemble Response ---
        data = {
            "metrics": {
                "total_employees": total_employees,
                "total_attendees": total_attendees,
            },
            "charts": {
                "employee_distribution": list(employee_dist),
                "payroll_distribution": list(payroll_dist),
            },
            "lists": {
                "tasks_due": tasks_due,
                # Serialize the recent activity logs
                "recent_activities": AuditLogSerializer(recent_activities, many=True).data,
            },
        }

        return Response(data, status=status.HTTP_200_OK)