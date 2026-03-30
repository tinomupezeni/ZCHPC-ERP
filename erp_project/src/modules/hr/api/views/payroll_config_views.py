"""
Payroll configuration API views (DeductionType, AllowanceType).
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.hr.infrastructure.persistence.models import DeductionType, AllowanceType


class DeductionTypeListCreateView(APIView):
    """
    List all deduction types or create a new one.

    GET /api/v2/hr/deductions/
    POST /api/v2/hr/deductions/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all deduction types."""
        deductions = DeductionType.objects.filter(is_active=True)
        data = [
            {
                'id': d.id,
                'name': d.name,
                'description': d.description,
                'is_percentage': d.is_percentage,
                'default_amount': str(d.default_amount) if d.default_amount else None,
            }
            for d in deductions
        ]
        return Response(data)

    def post(self, request):
        """Create a new deduction type."""
        name = request.data.get('name')
        description = request.data.get('description', '')
        is_percentage = request.data.get('is_percentage', False)
        default_amount = request.data.get('default_amount')

        if not name:
            return Response(
                {'error': 'Name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if DeductionType.objects.filter(name=name).exists():
            return Response(
                {'error': 'Deduction type with this name already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        deduction = DeductionType.objects.create(
            name=name,
            description=description,
            is_percentage=is_percentage,
            default_amount=default_amount,
        )

        return Response({
            'id': deduction.id,
            'name': deduction.name,
            'description': deduction.description,
            'is_percentage': deduction.is_percentage,
            'default_amount': str(deduction.default_amount) if deduction.default_amount else None,
        }, status=status.HTTP_201_CREATED)


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
            deduction = DeductionType.objects.get(id=deduction_id)
            return Response({
                'id': deduction.id,
                'name': deduction.name,
                'description': deduction.description,
                'is_percentage': deduction.is_percentage,
                'default_amount': str(deduction.default_amount) if deduction.default_amount else None,
            })
        except DeductionType.DoesNotExist:
            return Response(
                {'error': 'Deduction type not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, deduction_id):
        """Update a deduction type."""
        try:
            deduction = DeductionType.objects.get(id=deduction_id)
        except DeductionType.DoesNotExist:
            return Response(
                {'error': 'Deduction type not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if 'name' in request.data:
            deduction.name = request.data['name']
        if 'description' in request.data:
            deduction.description = request.data['description']
        if 'is_percentage' in request.data:
            deduction.is_percentage = request.data['is_percentage']
        if 'default_amount' in request.data:
            deduction.default_amount = request.data['default_amount']

        deduction.save()

        return Response({
            'id': deduction.id,
            'name': deduction.name,
            'description': deduction.description,
            'is_percentage': deduction.is_percentage,
            'default_amount': str(deduction.default_amount) if deduction.default_amount else None,
        })

    def delete(self, request, deduction_id):
        """Delete (deactivate) a deduction type."""
        try:
            deduction = DeductionType.objects.get(id=deduction_id)
            deduction.is_active = False
            deduction.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DeductionType.DoesNotExist:
            return Response(
                {'error': 'Deduction type not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AllowanceTypeListCreateView(APIView):
    """
    List all allowance types or create a new one.

    GET /api/v2/hr/allowances/
    POST /api/v2/hr/allowances/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all allowance types."""
        allowances = AllowanceType.objects.filter(is_active=True)
        data = [
            {
                'id': a.id,
                'name': a.name,
                'description': a.description,
                'is_taxable': a.is_taxable,
            }
            for a in allowances
        ]
        return Response(data)

    def post(self, request):
        """Create a new allowance type."""
        name = request.data.get('name')
        description = request.data.get('description', '')
        is_taxable = request.data.get('is_taxable', True)

        if not name:
            return Response(
                {'error': 'Name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if AllowanceType.objects.filter(name=name).exists():
            return Response(
                {'error': 'Allowance type with this name already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowance = AllowanceType.objects.create(
            name=name,
            description=description,
            is_taxable=is_taxable,
        )

        return Response({
            'id': allowance.id,
            'name': allowance.name,
            'description': allowance.description,
            'is_taxable': allowance.is_taxable,
        }, status=status.HTTP_201_CREATED)


class AllowanceTypeDetailView(APIView):
    """
    Retrieve, update or delete an allowance type.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, allowance_id):
        """Delete (deactivate) an allowance type."""
        try:
            allowance = AllowanceType.objects.get(id=allowance_id)
            allowance.is_active = False
            allowance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AllowanceType.DoesNotExist:
            return Response(
                {'error': 'Allowance type not found'},
                status=status.HTTP_404_NOT_FOUND
            )
