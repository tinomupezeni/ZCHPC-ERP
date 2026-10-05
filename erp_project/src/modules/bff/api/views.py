from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from modules.bff.orchestrators.employee_orchestrator import EmployeeOrchestrator
from modules.bff.serializers.unified_employee import UnifiedEmployeeProfileSerializer
from modules.payroll.api.actors import payroll_actor_from_request
from modules.payroll.api.errors import error_response
from shared.domain.exceptions import AuthorizationError, ValidationError
from modules.hr.application.authorization import (
    EmployeeAuthorizationPolicy,
    resolve_actor_permissions,
)

def _lifecycle_status(uuid):
    from modules.hr.infrastructure.persistence.models import Employees

    return Employees.objects.filter(uuid=uuid).values_list("lifecycle_status", flat=True).first()


def _not_found():
    return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)


class BFFEmployeeDetailView(APIView):
    def get(self, request, uuid):
        # An archived employee is visible only with hr.employee.view_archived (AUD-02).
        if _lifecycle_status(uuid) == "ARCHIVED" and not EmployeeAuthorizationPolicy().may_view_archived(
            resolve_actor_permissions(request.user)
        ):
            return _not_found()

        profile_data = EmployeeOrchestrator.get_full_profile(uuid, payroll_actor_from_request(request))

        if not profile_data:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UnifiedEmployeeProfileSerializer(data=profile_data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, uuid):
        # An archived employee's record is closed (AUD-02).
        if _lifecycle_status(uuid) == "ARCHIVED":
            if not EmployeeAuthorizationPolicy().may_view_archived(
                resolve_actor_permissions(request.user)
            ):
                return _not_found()
            return Response(
                {"error": "An archived employee cannot be edited", "code": "EMPLOYEE_ARCHIVED"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # We accept partial or full data from the frontend
        try:
            updated_profile_data = EmployeeOrchestrator.update_full_profile(
                uuid, request.data, payroll_actor_from_request(request)
            )
        except (AuthorizationError, ValidationError) as e:
            # ValidationError: the HR fields are validated by EmployeeService.
            return error_response(e)

        if not updated_profile_data:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UnifiedEmployeeProfileSerializer(data=updated_profile_data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
