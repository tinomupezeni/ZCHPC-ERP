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
    """
    A line item on a new purchase request.

    category_id is the employee-facing category and is required. There is no
    budget_code_id: the authoritative accounting code is assigned by Accounts,
    and unknown fields are ignored, so an employee cannot supply one. This is
    shape validation only; category existence/active-state is checked in
    CreatePurchaseRequest.
    """

    description = serializers.CharField(max_length=2000)
    quantity = serializers.IntegerField(min_value=1)
    expected_delivery_period = serializers.CharField(max_length=100)
    estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0
    )
    category_id = serializers.IntegerField(min_value=1)


class CreatePurchaseRequestInputSerializer(serializers.Serializer):
    """
    Input for raising a purchase request.

    Requester, department, designation and contact are intentionally absent:
    they are taken from the authenticated employee.
    """

    items = PurchaseRequestItemInputSerializer(many=True, allow_empty=True)


class UpdatePurchaseRequestItemInputSerializer(serializers.Serializer):
    """
    One item in a DRAFT/REJECTED item-collection replacement (Slice 2).

    No budget_code_id field at all: unlike create, this endpoint is
    exclusively the employee-facing edit path, so the direct-GL escape hatch
    create keeps for back-office callers has no reason to exist here -
    category_id is required, not one-of-two. `id` identifies an existing
    item on this request to update; omit it to add a new item. A supplied id
    that doesn't belong to this request, or a duplicate id in the same
    payload, is rejected by UpdatePurchaseRequestItems, not here - this is
    shape validation only.
    """

    id = serializers.IntegerField(min_value=1, required=False)
    description = serializers.CharField(max_length=2000)
    quantity = serializers.IntegerField(min_value=1)
    expected_delivery_period = serializers.CharField(max_length=100)
    estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0
    )
    category_id = serializers.IntegerField(min_value=1)


class UpdatePurchaseRequestInputSerializer(serializers.Serializer):
    """
    Input for replacing a DRAFT/REJECTED request's entire item collection
    (Slice 2). Full replacement: any existing item whose id isn't present
    here is removed.
    """

    items = UpdatePurchaseRequestItemInputSerializer(many=True, allow_empty=True)


class RejectPurchaseRequestInputSerializer(serializers.Serializer):
    """Input for rejecting a purchase request."""

    reason = serializers.CharField(max_length=2000, allow_blank=False)


class ProcessPurchaseRequestInputSerializer(serializers.Serializer):
    """
    Input for Procurement processing (F23).

    purchase_order_number is manually entered by the Procurement Officer -
    free text, not auto-generated like requisition_number. Shape validation
    only; required/non-blank and max length here, uniqueness and the
    PENDING_PROCUREMENT state check belong to
    ProcessPurchaseRequestByProcurement/the domain, not this serializer.
    """

    purchase_order_number = serializers.CharField(max_length=50, allow_blank=False)


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


class PurchaseRequestItemCategorySerializer(serializers.Serializer):
    """
    The employee-facing category an item's budget_code_id maps back to
    (Slice 2), so an edit form can pre-select it.

    Distinct from PurchaseRequestCategorySerializer (the category-list
    response) only because this one also reports is_active - the frontend
    needs that to decide whether the pre-filled category is still a legal
    choice, which the plain list endpoint (already filtered to active-only)
    never needs to say for itself. Still just id + name + is_active: no
    account_chart_id, no GL code, exactly the same disclosure boundary as
    the list endpoint.
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class PurchaseRequestItemBudgetCodeSerializer(serializers.Serializer):
    """id + code + name of the assigned AccountChart row (for the printed requisition)."""

    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class PurchaseRequestItemSerializer(serializers.Serializer):
    """A line item in a purchase request response."""

    id = serializers.IntegerField(read_only=True)
    description = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    expected_delivery_period = serializers.CharField(read_only=True)
    estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    category_id = serializers.IntegerField(read_only=True)
    budget_code_id = serializers.IntegerField(read_only=True, allow_null=True)
    budget_code = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    def to_representation(self, instance):
        """
        budget_code / budget_code_id are Finance/Procurement information. When
        the view did not grant them (context include_budget_code), the keys are
        omitted entirely - not nulled, which would read as "unassigned".
        """
        data = super().to_representation(instance)
        if not self.context.get("include_budget_code", False):
            data.pop("budget_code_id", None)
            data.pop("budget_code", None)
        return data

    def get_budget_code(self, obj) -> dict | None:
        """
        The Accounts-assigned AccountChart row, looked up by the item's own
        budget_code_id - never derived from the category. None while
        unassigned. The view passes budget_codes_by_id (one batched query).
        """
        if obj.budget_code_id is None:
            return None
        budget_code = self.context.get("budget_codes_by_id", {}).get(obj.budget_code_id)
        if budget_code is None:
            return None
        return PurchaseRequestItemBudgetCodeSerializer(budget_code).data

    def get_category(self, obj) -> dict | None:
        """
        The item's persisted employee-facing category. The view builds a
        {category_id: PurchaseRequestCategory} map once per response (avoiding
        an N+1 lookup per item) and passes it in as categories_by_id.
        """
        categories_by_id = self.context.get("categories_by_id", {})
        category = categories_by_id.get(obj.category_id)
        if category is None:
            return None
        return PurchaseRequestItemCategorySerializer(category).data


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
    purchase_order_number = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True, allow_null=True)


class AssignBudgetCodeInputSerializer(serializers.Serializer):
    """Input for Accounts assigning one item's budget code."""

    budget_code_id = serializers.IntegerField(min_value=1)


class BudgetCodeSerializer(serializers.Serializer):
    """An assignable AccountChart row, shown to Accounts only."""

    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    external_account_type = serializers.CharField(read_only=True)


class PurchaseRequestCategorySerializer(serializers.Serializer):
    """
    Employee-facing Purchase Request category response (Slice F11-A).

    Deliberately just id + name: account_chart_id, the GL code, and every
    other AccountChart field stay internal to the resolution the server
    performs on create - an employee never sees them here, and this
    serializer is the only place the category list reaches the client, so
    there is nowhere else that could leak them.
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


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
