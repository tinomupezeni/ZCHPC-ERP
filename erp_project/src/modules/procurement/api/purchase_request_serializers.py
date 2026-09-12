"""
Serializers for the redesigned Purchase Request API.

These handle data shape only - required fields, types, structural validation.
Workflow rules belong to the PurchaseRequest aggregate and access rules to the
Slice 4 authorization policy; neither is restated here.

Note that no input serializer accepts a requester, approver or actor id. The
acting employee is always derived from the authenticated request.
"""

from rest_framework import serializers

from modules.procurement.application.authorization import PurchaseRequestListScope


class PurchaseRequestItemInputSerializer(serializers.Serializer):
    """A line item on a new purchase request."""

    description = serializers.CharField(max_length=2000)
    quantity = serializers.IntegerField(min_value=1)
    expected_delivery_period = serializers.CharField(max_length=100)
    estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0
    )
    budget_code_id = serializers.IntegerField(min_value=1)


class CreatePurchaseRequestInputSerializer(serializers.Serializer):
    """
    Input for raising a purchase request.

    Requester, department, designation and contact are intentionally absent:
    they are taken from the authenticated employee.
    """

    items = PurchaseRequestItemInputSerializer(many=True, allow_empty=True)


class RejectPurchaseRequestInputSerializer(serializers.Serializer):
    """Input for rejecting a purchase request."""

    reason = serializers.CharField(max_length=2000, allow_blank=False)


class ListPurchaseRequestsQuerySerializer(serializers.Serializer):
    """Query parameters for the purchase request collection."""

    scope = serializers.ChoiceField(
        choices=[s.value for s in PurchaseRequestListScope],
        required=False,
        default=PurchaseRequestListScope.MINE.value,
    )

    def validated_scope(self) -> PurchaseRequestListScope:
        """The requested collection as a domain-level scope."""
        return PurchaseRequestListScope(self.validated_data["scope"])


class PurchaseRequestItemSerializer(serializers.Serializer):
    """A line item in a purchase request response."""

    id = serializers.IntegerField(read_only=True)
    description = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    expected_delivery_period = serializers.CharField(read_only=True)
    estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    budget_code_id = serializers.IntegerField(read_only=True)


class PurchaseRequestDecisionSerializer(serializers.Serializer):
    """One immutable workflow decision in a purchase request response."""

    id = serializers.IntegerField(read_only=True)
    stage = serializers.CharField(source="stage.value", read_only=True)
    decision = serializers.CharField(source="decision.value", read_only=True)
    actor_id = serializers.IntegerField(read_only=True)
    reason = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class PurchaseRequestSerializer(serializers.Serializer):
    """Full purchase request representation."""

    id = serializers.IntegerField(read_only=True)
    requisition_number = serializers.CharField(read_only=True)
    requester_id = serializers.IntegerField(read_only=True)
    requester_name = serializers.CharField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    department_name = serializers.CharField(read_only=True)
    designation = serializers.CharField(read_only=True)
    contact = serializers.CharField(read_only=True)
    status = serializers.CharField(source="status.value", read_only=True)
    total_estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    items = PurchaseRequestItemSerializer(many=True, read_only=True)
    decisions = PurchaseRequestDecisionSerializer(many=True, read_only=True)
    processed_by = serializers.IntegerField(read_only=True, allow_null=True)
    processed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True, allow_null=True)


class PurchaseRequestListSerializer(serializers.Serializer):
    """Condensed representation for collection responses."""

    id = serializers.IntegerField(read_only=True)
    requisition_number = serializers.CharField(read_only=True)
    requester_id = serializers.IntegerField(read_only=True)
    requester_name = serializers.CharField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    department_name = serializers.CharField(read_only=True)
    status = serializers.CharField(source="status.value", read_only=True)
    total_estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True, allow_null=True)
