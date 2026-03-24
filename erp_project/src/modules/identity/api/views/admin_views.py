"""
Admin dashboard API views.
"""
from datetime import date

from django.db.models import Count, Sum
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView


class AdminDashboardView(APIView):
    """
    API endpoint for admin dashboard aggregated data.

    GET /api/v2/admin/dashboard/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Return aggregated dashboard data.

        Response:
        {
            "metrics": {
                "total_employees": int,
                "total_attendees": int
            },
            "charts": {
                "employee_distribution": [...],
                "payroll_distribution": [...]
            },
            "lists": {
                "tasks_due": [...]
            }
        }
        """
        from modules.hr.infrastructure.persistence.models import Employees, Department
        from modules.attendance.infrastructure.persistence.models import AttendanceRecord
        from modules.payroll.infrastructure.persistence.models import Payroll

        # Metrics
        total_employees = Employees.objects.filter(is_active=True).count()

        # Today's attendance
        today = date.today()
        total_attendees = AttendanceRecord.objects.filter(
            date=today
        ).values('employee').distinct().count()

        # Employee distribution by department
        employee_distribution = list(
            Employees.objects.filter(is_active=True)
            .values('department__name')
            .annotate(employees=Count('id'))
            .order_by('-employees')
        )
        # Format for frontend
        employee_distribution = [
            {
                'department': item['department__name'] or 'Unassigned',
                'employees': item['employees']
            }
            for item in employee_distribution
        ]

        # Payroll distribution by department (latest period)
        payroll_distribution = list(
            Payroll.objects.values('employee__department__name')
            .annotate(
                total_usd=Sum('net_salary_usd'),
                total_zig=Sum('net_salary_zig')
            )
            .order_by('-total_usd')
        )
        # Format for frontend
        payroll_distribution = [
            {
                'employee__department': item['employee__department__name'] or 'Unassigned',
                'total_usd': str(item['total_usd'] or 0),
                'total_zig': str(item['total_zig'] or 0)
            }
            for item in payroll_distribution
        ]

        # Tasks due (placeholder - can be extended)
        tasks_due = [
            {
                'id': 1,
                'text': 'Review pending leave requests',
                'done': False,
                'module': 'hr',
                'due': 'Today'
            },
            {
                'id': 2,
                'text': 'Process monthly payroll',
                'done': False,
                'module': 'hr',
                'due': 'End of month'
            },
            {
                'id': 3,
                'text': 'Update employee records',
                'done': False,
                'module': 'hr',
                'due': 'This week'
            },
        ]

        return Response({
            'metrics': {
                'total_employees': total_employees,
                'total_attendees': total_attendees,
            },
            'charts': {
                'employee_distribution': employee_distribution,
                'payroll_distribution': payroll_distribution,
            },
            'lists': {
                'tasks_due': tasks_due,
            }
        }, status=status.HTTP_200_OK)
