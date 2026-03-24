"""
Organization API views (Department, Position).
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.exceptions import NotFoundError, ValidationError

from modules.hr.api.serializers import (
    CreateDepartmentRequestSerializer,
    CreatePositionRequestSerializer,
    DepartmentResponseSerializer,
    PositionResponseSerializer,
    UpdateDepartmentRequestSerializer,
    UpdatePositionRequestSerializer,
)
from modules.hr.application.services import (
    CreateDepartmentCommand,
    CreatePositionCommand,
    DepartmentService,
    PositionService,
    UpdateDepartmentCommand,
    UpdatePositionCommand,
)
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository


def get_department_service() -> DepartmentService:
    """Factory function to create DepartmentService with dependencies."""
    return DepartmentService(
        department_repository=DjangoDepartmentRepository(),
        employee_repository=DjangoEmployeeRepository(),
    )


def get_position_service() -> PositionService:
    """Factory function to create PositionService with dependencies."""
    return PositionService(
        position_repository=DjangoPositionRepository(),
        department_repository=DjangoDepartmentRepository(),
        employee_repository=DjangoEmployeeRepository(),
    )


# =============================================================================
# Department Views
# =============================================================================


class DepartmentListCreateView(APIView):
    """
    List all departments or create a new department.

    GET: List all departments
    POST: Create a new department
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all departments."""
        service = get_department_service()
        departments = service.get_all_departments()
        serializer = DepartmentResponseSerializer(departments, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new department."""
        serializer = CreateDepartmentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = get_department_service()

        try:
            command = CreateDepartmentCommand(**serializer.validated_data)
            department = service.create_department(command)

            response_data = {
                "id": department.id,
                "name": department.name,
                "description": department.description,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            import logging
            logging.exception("Error creating department")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DepartmentDetailView(APIView):
    """
    Retrieve, update, or delete a department.

    GET: Get department details
    PUT/PATCH: Update department
    DELETE: Delete department
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, department_id: int):
        """Get department details."""
        service = get_department_service()
        department = service.get_department(department_id)

        if not department:
            return Response(
                {"error": "Department not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DepartmentResponseSerializer(department)
        return Response(serializer.data)

    def put(self, request, department_id: int):
        """Update department (full update)."""
        return self._update(request, department_id)

    def patch(self, request, department_id: int):
        """Update department (partial update)."""
        return self._update(request, department_id)

    def _update(self, request, department_id: int):
        """Handle department update."""
        serializer = UpdateDepartmentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = get_department_service()

        try:
            command = UpdateDepartmentCommand(
                department_id=department_id,
                **serializer.validated_data,
            )
            department = service.update_department(command)

            response_data = {
                "id": department.id,
                "name": department.name,
                "description": department.description,
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

    def delete(self, request, department_id: int):
        """Delete a department."""
        service = get_department_service()

        try:
            deleted = service.delete_department(department_id)
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"error": "Failed to delete department"},
                status=status.HTTP_400_BAD_REQUEST,
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


# =============================================================================
# Position Views
# =============================================================================


class PositionListCreateView(APIView):
    """
    List all positions or create a new position.

    GET: List positions (optionally filtered by department)
    POST: Create a new position
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List positions."""
        service = get_position_service()

        department_id = request.query_params.get("department_id")

        if department_id:
            positions = service.get_positions_by_department(int(department_id))
        else:
            # Get all positions
            repo = DjangoPositionRepository()
            dept_repo = DjangoDepartmentRepository()
            all_positions = repo.get_all()
            positions = []
            for pos in all_positions:
                dept = dept_repo.get_by_id(pos.department_id)
                positions.append({
                    "id": pos.id,
                    "title": pos.title,
                    "department_id": pos.department_id,
                    "department_name": dept.name if dept else "",
                    "description": pos.description,
                })

        serializer = PositionResponseSerializer(positions, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new position."""
        serializer = CreatePositionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = get_position_service()

        try:
            command = CreatePositionCommand(**serializer.validated_data)
            position = service.create_position(command)

            response_data = {
                "id": position.id,
                "title": position.title,
                "department_id": position.department_id,
                "description": position.description,
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


class PositionDetailView(APIView):
    """
    Retrieve, update, or delete a position.

    GET: Get position details
    PUT/PATCH: Update position
    DELETE: Delete position
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, position_id: int):
        """Get position details."""
        service = get_position_service()
        position = service.get_position(position_id)

        if not position:
            return Response(
                {"error": "Position not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PositionResponseSerializer(position)
        return Response(serializer.data)

    def put(self, request, position_id: int):
        """Update position (full update)."""
        return self._update(request, position_id)

    def patch(self, request, position_id: int):
        """Update position (partial update)."""
        return self._update(request, position_id)

    def _update(self, request, position_id: int):
        """Handle position update."""
        serializer = UpdatePositionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = get_position_service()

        try:
            command = UpdatePositionCommand(
                position_id=position_id,
                **serializer.validated_data,
            )
            position = service.update_position(command)

            response_data = {
                "id": position.id,
                "title": position.title,
                "department_id": position.department_id,
                "description": position.description,
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

    def delete(self, request, position_id: int):
        """Delete a position."""
        service = get_position_service()

        try:
            deleted = service.delete_position(position_id)
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"error": "Failed to delete position"},
                status=status.HTTP_400_BAD_REQUEST,
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


# =============================================================================
# Role Views
# =============================================================================


class RoleListCreateView(APIView):
    """
    List all roles or create a new role.

    GET: List all roles
    POST: Create a new role
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all roles."""
        from modules.hr.infrastructure.persistence.models import Role

        roles = Role.objects.all()
        data = [
            {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "permissions": role.permissions,
            }
            for role in roles
        ]
        return Response(data)

    def post(self, request):
        """Create a new role."""
        from modules.hr.infrastructure.persistence.models import Role

        name = request.data.get("name")
        display_name = request.data.get("display_name", name)
        description = request.data.get("description", "")
        permissions = request.data.get("permissions", [])

        if not name:
            return Response(
                {"error": "Name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Role.objects.filter(name=name).exists():
            return Response(
                {"error": f"Role with name '{name}' already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = Role.objects.create(
            name=name,
            display_name=display_name,
            description=description,
            permissions=permissions,
        )

        return Response(
            {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "permissions": role.permissions,
            },
            status=status.HTTP_201_CREATED,
        )


class RoleDetailView(APIView):
    """
    Retrieve, update, or delete a role.

    GET: Get role details
    PUT/PATCH: Update role
    DELETE: Delete role
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, role_id: int):
        """Get role details."""
        from modules.hr.infrastructure.persistence.models import Role

        try:
            role = Role.objects.get(id=role_id)
            return Response({
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "permissions": role.permissions,
            })
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(self, request, role_id: int):
        """Update role (full update)."""
        return self._update(request, role_id)

    def patch(self, request, role_id: int):
        """Update role (partial update)."""
        return self._update(request, role_id)

    def _update(self, request, role_id: int):
        """Handle role update."""
        from modules.hr.infrastructure.persistence.models import Role

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if "name" in request.data:
            role.name = request.data["name"]
        if "display_name" in request.data:
            role.display_name = request.data["display_name"]
        if "description" in request.data:
            role.description = request.data["description"]
        if "permissions" in request.data:
            role.permissions = request.data["permissions"]

        role.save()

        return Response({
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "permissions": role.permissions,
        })

    def delete(self, request, role_id: int):
        """Delete a role."""
        from modules.hr.infrastructure.persistence.models import Role

        try:
            role = Role.objects.get(id=role_id)
            role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
