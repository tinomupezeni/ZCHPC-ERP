"""
Payroll configuration API views (DeductionType, AllowanceType).

These administer the same tables as the payroll module's own allowance and
deduction endpoints, so they go through the same PayrollConfigurationService
and its payroll authorization policy (REM-02): reaching the hr routes at all
is not enough to read or change payroll configuration.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.payroll.api.actors import payroll_actor_from_request
from modules.payroll.api.errors import error_response
from modules.payroll.application.services.payroll_configuration_service import (
    PayrollConfigurationService,
)
from shared.domain.exceptions import DomainException

_configuration = PayrollConfigurationService()


def _deduction_payload(d):
    return {
        'id': d.id,
        'name': d.name,
        'description': d.description,
        'is_percentage': d.is_percentage,
        'default_amount': str(d.default_amount) if d.default_amount else None,
    }


def _allowance_payload(a):
    return {
        'id': a.id,
        'name': a.name,
        'description': a.description,
        'is_taxable': a.is_taxable,
    }


class DeductionTypeListCreateView(APIView):
    """
    List all deduction types or create a new one.

    GET /api/v2/hr/deductions/
    POST /api/v2/hr/deductions/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all deduction types."""
        try:
            deductions = _configuration.list_deduction_types(
                payroll_actor_from_request(request), active_only=True
            )
        except DomainException as e:
            return error_response(e)
        return Response([_deduction_payload(d) for d in deductions])

    def post(self, request):
        """Create a new deduction type."""
        try:
            deduction = _configuration.create_deduction_type(
                payroll_actor_from_request(request),
                name=request.data.get('name'),
                description=request.data.get('description', ''),
                is_percentage=request.data.get('is_percentage', False),
                default_amount=request.data.get('default_amount'),
            )
        except DomainException as e:
            return error_response(e)

        return Response(_deduction_payload(deduction), status=status.HTTP_201_CREATED)


class DeductionTypeDetailView(APIView):
    """
    Retrieve, update or delete a deduction type.

    GET /api/v2/hr/deductions/<id>/
    PATCH /api/v2/hr/deductions/<id>/
    DELETE /api/v2/hr/deductions/<id>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, deduction_id):
        """Get a specific deduction type."""
        try:
            deduction = _configuration.get_deduction_type(
                payroll_actor_from_request(request), deduction_id
            )
        except DomainException as e:
            return error_response(e)
        return Response(_deduction_payload(deduction))

    def patch(self, request, deduction_id):
        """Update a deduction type."""
        changes = {
            key: request.data[key]
            for key in ('name', 'description', 'is_percentage', 'default_amount')
            if key in request.data
        }
        try:
            deduction = _configuration.update_deduction_type(
                payroll_actor_from_request(request), deduction_id, changes
            )
        except DomainException as e:
            return error_response(e)
        return Response(_deduction_payload(deduction))

    def delete(self, request, deduction_id):
        """Delete (deactivate) a deduction type."""
        try:
            _configuration.deactivate_deduction_type(
                payroll_actor_from_request(request), deduction_id
            )
        except DomainException as e:
            return error_response(e)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AllowanceTypeListCreateView(APIView):
    """
    List all allowance types or create a new one.

    GET /api/v2/hr/allowances/
    POST /api/v2/hr/allowances/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all allowance types."""
        try:
            allowances = _configuration.list_allowance_types(
                payroll_actor_from_request(request), active_only=True
            )
        except DomainException as e:
            return error_response(e)
        return Response([_allowance_payload(a) for a in allowances])

    def post(self, request):
        """Create a new allowance type."""
        try:
            allowance = _configuration.create_allowance_type(
                payroll_actor_from_request(request),
                name=request.data.get('name'),
                description=request.data.get('description', ''),
                is_taxable=request.data.get('is_taxable', True),
            )
        except DomainException as e:
            return error_response(e)

        return Response(_allowance_payload(allowance), status=status.HTTP_201_CREATED)


class AllowanceTypeDetailView(APIView):
    """
    Retrieve, update or delete an allowance type.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, allowance_id):
        """Delete (deactivate) an allowance type."""
        try:
            _configuration.deactivate_allowance_type(
                payroll_actor_from_request(request), allowance_id
            )
        except DomainException as e:
            return error_response(e)
        return Response(status=status.HTTP_204_NO_CONTENT)
