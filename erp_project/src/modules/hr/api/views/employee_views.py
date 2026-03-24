"""
Employee API views.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.exceptions import NotFoundError, ValidationError

from modules.hr.api.serializers import (
    CreateEmployeeRequestSerializer,
    EmployeeListItemSerializer,
    EmployeeResponseSerializer,
    SalarySerializer,
    UpdateEmployeeRequestSerializer,
)
from modules.hr.application.services import (
    CreateEmployeeCommand,
    EmployeeService,
    UpdateEmployeeCommand,
)
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository


def get_employee_service() -> EmployeeService:
    """Factory function to create EmployeeService with dependencies."""
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


class EmployeeListCreateView(APIView):
    """
    List all employees or create a new employee.

    GET: List all active employees
    POST: Create a new employee
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all active employees."""
        service = get_employee_service()

        # Optional filters
        department_id = request.query_params.get("department_id")
        include_inactive = request.query_params.get("include_inactive", "false").lower() == "true"

        if department_id:
            employees = service.get_employees_by_department(int(department_id))
        else:
            employees = service.get_active_employees()

        # If include_inactive, get all
        if include_inactive:
            repo = DjangoEmployeeRepository()
            all_employees = repo.get_all(include_inactive=True)
            employees = [service._to_dto(e) for e in all_employees]

        serializer = EmployeeListItemSerializer(employees, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new employee."""
        serializer = CreateEmployeeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = get_employee_service()

        try:
            command = CreateEmployeeCommand(**serializer.validated_data)
            employee = service.create_employee(command)

            # Convert to response DTO
            response_data = {
                "id": employee.id,
                "employee_id": str(employee.employee_id),
                "first_name": employee.first_name,
                "surname": employee.surname,
                "full_name": employee.full_name,
                "email": employee.email.value if employee.email else None,
                "department_id": employee.department_id,
                "position_id": employee.position_id,
                "is_active": employee.is_active,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )


class EmployeeDetailView(APIView):
    """
    Retrieve, update, or delete an employee.

    GET: Get employee details
    PUT/PATCH: Update employee
    DELETE: Deactivate employee (soft delete)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id: int):
        """Get employee details."""
        service = get_employee_service()
        employee = service.get_employee(employee_id)

        if not employee:
            return Response(
                {"error": "Employee not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EmployeeResponseSerializer(employee)
        return Response(serializer.data)

    def put(self, request, employee_id: int):
        """Update employee (full update)."""
        return self._update(request, employee_id)

    def patch(self, request, employee_id: int):
        """Update employee (partial update)."""
        return self._update(request, employee_id)

    def _update(self, request, employee_id: int):
        """Handle employee update."""
        serializer = UpdateEmployeeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = get_employee_service()

        try:
            command = UpdateEmployeeCommand(
                employee_id=employee_id,
                **serializer.validated_data,
            )
            employee = service.update_employee(command)

            response_data = {
                "id": employee.id,
                "employee_id": str(employee.employee_id),
                "first_name": employee.first_name,
                "surname": employee.surname,
                "full_name": employee.full_name,
                "is_active": employee.is_active,
            }

            return Response(response_data)

        except NotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, employee_id: int):
        """Deactivate an employee (soft delete)."""
        service = get_employee_service()
        reason = request.data.get("reason", "")

        try:
            employee = service.deactivate_employee(employee_id, reason)
            return Response(
                {"message": f"Employee {employee.full_name} deactivated"},
                status=status.HTTP_200_OK,
            )
        except NotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )


class EmployeeSalaryView(APIView):
    """
    Get or update employee salary.

    GET: Get employee salary
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id: int):
        """Get employee salary."""
        service = get_employee_service()
        salary = service.get_employee_salary(employee_id)

        if not salary:
            return Response(
                {"error": "Employee or salary not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SalarySerializer(salary)
        return Response(serializer.data)
