"""
Employee API views.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.exceptions import AuthorizationError, NotFoundError, ValidationError

from modules.hr.api.serializers import (
    CreateEmployeeRequestSerializer,
    EmployeeListItemSerializer,
    EmployeeResponseSerializer,
    SalarySerializer,
    UpdateEmployeeRequestSerializer,
)
from modules.hr.application.authorization import resolve_actor_permissions
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


def _actor_employee_id(request) -> int | None:
    """The authenticated caller's own employee record id - never from request data."""
    # Reverse one-to-one: an AttributeError subclass when there is no profile.
    employee = getattr(request.user, "employee_profile", None)
    return employee.pk if employee else None


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
        actor_permissions = resolve_actor_permissions(request.user)

        # Optional filters
        department_id = request.query_params.get("department_id")
        include_inactive = request.query_params.get("include_inactive", "false").lower() == "true"

        if department_id:
            employees = service.get_employees_by_department(
                int(department_id), actor_permissions=actor_permissions
            )
        else:
            employees = service.get_active_employees(actor_permissions=actor_permissions)

        # If include_inactive, get all
        if include_inactive:
            repo = DjangoEmployeeRepository()
            all_employees = repo.get_all(include_inactive=True)
            employees = [service._to_dto(e, actor_permissions) for e in all_employees]

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
            employee = service.create_employee(
                command,
                actor_permissions=resolve_actor_permissions(request.user),
                actor_email=request.user.email,
            )

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
                # One-time temporary password of the login provisioned for
                # this employee (null if none was created); shown once to the
                # creator, who must hand it over. REM-07.
                "temporary_password": employee.temporary_password,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except AuthorizationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_403_FORBIDDEN,
            )
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
        employee = service.get_employee(
            employee_id, actor_permissions=resolve_actor_permissions(request.user)
        )

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
        actor_permissions = resolve_actor_permissions(request.user)

        try:
            command = UpdateEmployeeCommand(
                employee_id=employee_id,
                **serializer.validated_data,
            )
            employee = service.update_employee(
                command,
                actor_permissions=actor_permissions,
                actor_employee_id=_actor_employee_id(request),
            )

            response_data = {
                "id": employee.id,
                "employee_id": str(employee.employee_id),
                "first_name": employee.first_name,
                "surname": employee.surname,
                "full_name": employee.full_name,
                "is_active": employee.is_active,
            }

            return Response(response_data)

        except AuthorizationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_403_FORBIDDEN,
            )
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
            employee = service.deactivate_employee(
                employee_id,
                reason,
                actor_permissions=resolve_actor_permissions(request.user),
                actor_employee_id=_actor_employee_id(request),
            )
            return Response(
                {"message": f"Employee {employee.full_name} deactivated"},
                status=status.HTTP_200_OK,
            )
        except AuthorizationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_403_FORBIDDEN,
            )
        except NotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            # e.g. the employee is archived (AUD-02): not a deactivation target
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )


class EmployeeReactivateView(APIView):
    """
    Reactivate a deactivated employee (AUD-02).

    POST: DEACTIVATED -> ACTIVE, re-enabling the employee's login
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, employee_id: int):
        """Reactivate an employee (needs hr.employee.reactivate, checked by EmployeeService)."""
        service = get_employee_service()

        try:
            result = service.reactivate_employee(
                employee_id,
                actor_permissions=resolve_actor_permissions(request.user),
                actor_employee_id=_actor_employee_id(request),
            )
        except AuthorizationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_403_FORBIDDEN,
            )
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

        employee = result.employee
        return Response(
            {
                "id": employee.id,
                "employee_id": str(employee.employee_id),
                "full_name": employee.full_name,
                "is_active": employee.is_active,
                "lifecycle_status": employee.lifecycle_status.value,
                # One-time temporary password of the re-enabled login (null
                # if no login was re-enabled); the owner must replace it at
                # first sign-in. REM-07.
                "temporary_password": result.temporary_password,
            },
            status=status.HTTP_200_OK,
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
        try:
            salary = service.get_employee_salary(
                employee_id, resolve_actor_permissions(request.user)
            )
        except AuthorizationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not salary:
            return Response(
                {"error": "Employee or salary not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SalarySerializer(salary)
        return Response(serializer.data)
