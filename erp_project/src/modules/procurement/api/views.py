"""
API views for the procurement module.
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.utils import timezone

from shared.domain.exceptions import ValidationError, NotFoundError
from modules.procurement.domain.entities import Supplier, InventoryItem, BudgetCenter
from modules.procurement.application.services import (
    ProcurementService,
    CreatePurchaseRequestDTO,
    RequestItemDTO,
)
from modules.procurement.infrastructure.persistence.django_supplier_repository import DjangoSupplierRepository
from modules.procurement.infrastructure.persistence.django_inventory_item_repository import DjangoInventoryItemRepository
from modules.procurement.infrastructure.persistence.django_budget_center_repository import DjangoBudgetCenterRepository
from modules.procurement.infrastructure.persistence.django_purchase_request_repository import DjangoPurchaseRequestRepository
from modules.procurement.infrastructure.persistence.django_purchase_order_repository import DjangoPurchaseOrderRepository
from modules.procurement.infrastructure.persistence.models import FuelRequisition, StoresRequisition, ComparativeSchedule
from modules.procurement.api.serializers import (
    SupplierSerializer,
    CreateSupplierSerializer,
    UpdateSupplierSerializer,
    InventoryItemSerializer,
    CreateInventoryItemSerializer,
    UpdateInventoryItemSerializer,
    BudgetCenterSerializer,
    CreateBudgetCenterSerializer,
    UpdateBudgetCenterSerializer,
    PurchaseRequestSerializer,
    CreatePurchaseRequestSerializer,
    ApproveRequestSerializer,
    RejectRequestSerializer,
    PurchaseOrderSerializer,
    MarkDeliveredSerializer,
    CancelOrderSerializer,
)


# Initialize repositories
_supplier_repo = DjangoSupplierRepository()
_item_repo = DjangoInventoryItemRepository()
_budget_repo = DjangoBudgetCenterRepository()
_request_repo = DjangoPurchaseRequestRepository()
_order_repo = DjangoPurchaseOrderRepository()

# Initialize service
_procurement_service = ProcurementService(
    supplier_repo=_supplier_repo,
    item_repo=_item_repo,
    budget_repo=_budget_repo,
    request_repo=_request_repo,
    order_repo=_order_repo,
)


def _handle_error(e: Exception) -> Response:
    """Handle domain exceptions."""
    if isinstance(e, ValidationError):
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    elif isinstance(e, NotFoundError):
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================
# Supplier Views
# ============================

@api_view(["GET", "POST"])
def supplier_list(request: Request) -> Response:
    """List suppliers or create a new supplier."""
    if request.method == "GET":
        include_inactive = (
            request.query_params.get("include_inactive", "false").lower() == "true"
        )
        search = request.query_params.get("search")

        if search:
            suppliers = _supplier_repo.search(search)
        else:
            suppliers = _supplier_repo.get_all(include_inactive=include_inactive)

        return Response(SupplierSerializer(suppliers, many=True).data)

    elif request.method == "POST":
        serializer = CreateSupplierSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            supplier = Supplier.create(**serializer.validated_data)
            saved = _supplier_repo.save(supplier)
            return Response(
                SupplierSerializer(saved).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return _handle_error(e)


@api_view(["GET", "PUT", "DELETE"])
def supplier_detail(request: Request, supplier_id: int) -> Response:
    """Get, update, or delete a supplier."""
    supplier = _supplier_repo.get_by_id(supplier_id)
    if supplier is None:
        return Response(
            {"error": "Supplier not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        return Response(SupplierSerializer(supplier).data)

    elif request.method == "PUT":
        serializer = UpdateSupplierSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            if "name" in data or "email" in data or "phone" in data or "address" in data:
                supplier.update_details(
                    name=data.get("name"),
                    email=data.get("email"),
                    phone=data.get("phone"),
                    address=data.get("address")
                )
            if "rating" in data:
                supplier.update_rating(data["rating"])

            saved = _supplier_repo.save(supplier)
            return Response(SupplierSerializer(saved).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "DELETE":
        supplier.deactivate()
        _supplier_repo.save(supplier)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def supplier_activate(request: Request, supplier_id: int) -> Response:
    """Activate a deactivated supplier."""
    supplier = _supplier_repo.get_by_id(supplier_id)
    if supplier is None:
        return Response(
            {"error": "Supplier not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    supplier.activate()
    saved = _supplier_repo.save(supplier)
    return Response(SupplierSerializer(saved).data)


# ============================
# Inventory Item Views
# ============================

@api_view(["GET", "POST"])
def inventory_item_list(request: Request) -> Response:
    """List inventory items or create a new item."""
    if request.method == "GET":
        low_stock = request.query_params.get("low_stock", "false").lower() == "true"

        if low_stock:
            items = _item_repo.get_low_stock()
        else:
            items = _item_repo.get_all()

        return Response(InventoryItemSerializer(items, many=True).data)

    elif request.method == "POST":
        serializer = CreateInventoryItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = InventoryItem.create(**serializer.validated_data)
            saved = _item_repo.save(item)
            return Response(
                InventoryItemSerializer(saved).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return _handle_error(e)


@api_view(["GET", "PUT", "DELETE"])
def inventory_item_detail(request: Request, item_id: int) -> Response:
    """Get, update, or delete an inventory item."""
    item = _item_repo.get_by_id(item_id)
    if item is None:
        return Response(
            {"error": "Inventory item not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        return Response(InventoryItemSerializer(item).data)

    elif request.method == "PUT":
        serializer = UpdateInventoryItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            if "name" in data:
                item.name = data["name"]
            if "quantity" in data:
                item.quantity = data["quantity"]
            if "price_per_unit" in data:
                item.price_per_unit = data["price_per_unit"]
            if "reorder_level" in data:
                item.reorder_level = data["reorder_level"]

            saved = _item_repo.save(item)
            return Response(InventoryItemSerializer(saved).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "DELETE":
        _item_repo.delete(item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================
# Budget Center Views
# ============================

@api_view(["GET", "POST"])
def budget_center_list(request: Request) -> Response:
    """List budget centers or create a new budget center."""
    if request.method == "GET":
        fiscal_year = request.query_params.get("fiscal_year")

        if fiscal_year:
            centers = _budget_repo.get_by_fiscal_year(int(fiscal_year))
        else:
            centers = _budget_repo.get_all()

        return Response(BudgetCenterSerializer(centers, many=True).data)

    elif request.method == "POST":
        serializer = CreateBudgetCenterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            center = BudgetCenter.create(**serializer.validated_data)
            saved = _budget_repo.save(center)
            return Response(
                BudgetCenterSerializer(saved).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return _handle_error(e)


@api_view(["GET", "PUT", "DELETE"])
def budget_center_detail(request: Request, center_id: int) -> Response:
    """Get, update, or delete a budget center."""
    center = _budget_repo.get_by_id(center_id)
    if center is None:
        return Response(
            {"error": "Budget center not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        return Response(BudgetCenterSerializer(center).data)

    elif request.method == "PUT":
        serializer = UpdateBudgetCenterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            if "name" in data:
                center.name = data["name"]
            if "allocated_amount" in data:
                center.allocated_amount = data["allocated_amount"]

            saved = _budget_repo.save(center)
            return Response(BudgetCenterSerializer(saved).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "DELETE":
        _budget_repo.delete(center_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================
# Purchase Request Views
# ============================

@api_view(["GET", "POST"])
def purchase_request_list(request: Request) -> Response:
    """List purchase requests or create a new request."""
    if request.method == "GET":
        status_filter = request.query_params.get("status")
        budget_center_id = request.query_params.get("budget_center_id")
        pending_level = request.query_params.get("pending_level")

        try:
            if pending_level:
                requests = _procurement_service.get_pending_approvals(
                    level=int(pending_level)
                )
            else:
                requests = _procurement_service.list_requests(
                    status=status_filter,
                    budget_center_id=int(budget_center_id) if budget_center_id else None
                )
            return Response(PurchaseRequestSerializer(requests, many=True).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "POST":
        serializer = CreatePurchaseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            items = [
                RequestItemDTO(
                    item_id=item["item_id"],
                    quantity=item["quantity"]
                )
                for item in data.get("items", [])
            ]

            dto = CreatePurchaseRequestDTO(
                requester_id=data["requester_id"],
                requester_name=data["requester_name"],
                supplier_id=data["supplier_id"],
                budget_center_id=data["budget_center_id"],
                items=items
            )

            pr = _procurement_service.create_purchase_request(dto)
            return Response(
                PurchaseRequestSerializer(pr).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return _handle_error(e)


@api_view(["GET", "DELETE"])
def purchase_request_detail(request: Request, request_id: int) -> Response:
    """Get or delete a purchase request."""
    if request.method == "GET":
        try:
            pr = _procurement_service.get_request(request_id)
            return Response(PurchaseRequestSerializer(pr).data)
        except Exception as e:
            return _handle_error(e)

    elif request.method == "DELETE":
        if _request_repo.delete(request_id):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"error": "Cannot delete non-pending request"},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(["POST"])
def purchase_request_approve_level1(request: Request, request_id: int) -> Response:
    """Approve a purchase request at Level 1."""
    serializer = ApproveRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        pr = _procurement_service.approve_level1(
            request_id=request_id,
            approver_id=serializer.validated_data["approver_id"]
        )
        return Response(PurchaseRequestSerializer(pr).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def purchase_request_approve_level2(request: Request, request_id: int) -> Response:
    """Approve a purchase request at Level 2 (creates Purchase Order)."""
    serializer = ApproveRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        pr, order = _procurement_service.approve_level2(
            request_id=request_id,
            approver_id=serializer.validated_data["approver_id"]
        )
        return Response({
            "request": PurchaseRequestSerializer(pr).data,
            "order": PurchaseOrderSerializer(order).data
        })
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def purchase_request_reject(request: Request, request_id: int) -> Response:
    """Reject a purchase request."""
    serializer = RejectRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        pr = _procurement_service.reject_request(
            request_id=request_id,
            rejector_id=serializer.validated_data["rejector_id"],
            reason=serializer.validated_data.get("reason")
        )
        return Response(PurchaseRequestSerializer(pr).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fuel_requisition_approve(request: Request, requisition_id: int) -> Response:
    """Approve exactly the current office stage of a fuel requisition."""
    try:
        record = FuelRequisition.objects.get(pk=requisition_id)
    except FuelRequisition.DoesNotExist:
        return Response({"error": "Fuel requisition not found"}, status=status.HTTP_404_NOT_FOUND)

    employee = getattr(request.user, "employee_profile", None)
    role = (employee.role.name if employee and employee.role else "").upper()
    is_admin = request.user.is_superuser or role in {"ADMIN", "SYSTEM_ADMINISTRATOR"}
    stages = {
        "PENDING_DEPARTMENT": ("department", {"MANAGER", "DEPARTMENT_MANAGER", "HR_MANAGER"}),
        "PENDING_RECIPIENT": ("recipient", set()),
        "PENDING_FINANCE": ("finance", {"FINANCE", "ACCOUNTANT", "GENERAL_MANAGER"}),
        "PENDING_DIRECTOR": ("director", {"DIRECTOR", "ZCHPC_DIRECTOR"}),
        "PENDING_ADMIN": ("admin", {"ADMIN", "SYSTEM_ADMINISTRATOR"}),
    }
    stage = stages.get(record.status)
    if stage is None:
        return Response({"error": "This requisition is no longer awaiting approval"}, status=status.HTTP_400_BAD_REQUEST)
    stage_name, roles = stage

    recipient_match = False
    if employee and stage_name == "recipient":
        recipient_text = record.recipient_driver.strip().lower()
        recipient_match = recipient_text in {
            request.user.email.lower(),
            f"{employee.first_name} {employee.surname}".strip().lower(),
            employee.employee_id.lower(),
        }
    if not is_admin and not (role in roles or any(item in role for item in roles) or recipient_match):
        return Response({"error": "You are not authorized for this approval stage"}, status=status.HTTP_403_FORBIDDEN)
    if record.requester_id == request.user.id:
        return Response({"error": "The requester cannot approve their own requisition"}, status=status.HTTP_403_FORBIDDEN)

    next_status = {
        "department": "PENDING_RECIPIENT",
        "recipient": "PENDING_FINANCE",
        "finance": "PENDING_DIRECTOR",
        "director": "PENDING_ADMIN",
        "admin": "APPROVED",
    }[stage_name]
    setattr(record, f"{stage_name}_approved_by_id", request.user.id)
    setattr(record, f"{stage_name}_approved_at", timezone.now())
    record.status = next_status
    record.save()
    return Response({"id": record.id, "status": record.status})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stores_requisition_approve(request: Request, requisition_id: int) -> Response:
    """Approve exactly the current office stage of a Stores Requisition."""
    try:
        record = StoresRequisition.objects.get(pk=requisition_id)
    except StoresRequisition.DoesNotExist:
        return Response({"error": "Stores requisition not found"}, status=status.HTTP_404_NOT_FOUND)

    employee = getattr(request.user, "employee_profile", None)
    role = (employee.role.name if employee and employee.role else "").upper()
    is_admin = request.user.is_superuser or role in {"ADMIN", "SYSTEM_ADMINISTRATOR"}
    stages = {
        "PENDING_DEPARTMENT": ("department", {"MANAGER", "DEPARTMENT_MANAGER", "HR_MANAGER"}),
        "PENDING_PROCUREMENT": ("procurement", {"PROCUREMENT", "PROCUREMENT_OFFICER", "STORES", "STORES_OFFICER"}),
        "PENDING_ACCOUNTS": ("accounts", {"ACCOUNTS", "ACCOUNTANT", "FINANCE"}),
        "PENDING_GENERAL_MANAGER": ("general_manager", {"GENERAL_MANAGER", "MANAGER"}),
        "PENDING_DIRECTOR": ("director", {"DIRECTOR", "ZCHPC_DIRECTOR"}),
        "PENDING_ADMIN": ("admin", {"ADMIN", "SYSTEM_ADMINISTRATOR"}),
    }
    stage = stages.get(record.status)
    if stage is None:
        return Response({"error": "This requisition is no longer awaiting approval"}, status=status.HTTP_400_BAD_REQUEST)
    stage_name, allowed_roles = stage
    if not is_admin and not (role in allowed_roles or any(item in role for item in allowed_roles)):
        return Response({"error": "You are not authorized for this approval stage"}, status=status.HTTP_403_FORBIDDEN)
    if stage_name == "department" and not is_admin and employee.department_id != record.department_id:
        return Response({"error": "Only the requester's department can approve this stage"}, status=status.HTTP_403_FORBIDDEN)
    if record.requester_id == request.user.id:
        return Response({"error": "The requester cannot approve their own requisition"}, status=status.HTTP_403_FORBIDDEN)

    next_status = {
        "department": "PENDING_PROCUREMENT",
        "procurement": "PENDING_ACCOUNTS",
        "accounts": "PENDING_GENERAL_MANAGER",
        "general_manager": "PENDING_DIRECTOR",
        "director": "PENDING_ADMIN",
        "admin": "APPROVED",
    }[stage_name]
    setattr(record, f"{stage_name}_approved_by_id", request.user.id)
    setattr(record, f"{stage_name}_approved_at", timezone.now())
    record.status = next_status
    record.save()
    return Response({"id": record.id, "requisition_number": record.requisition_number, "status": record.status})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def comparative_schedule_approve(request: Request, schedule_id: int) -> Response:
    """Advance a comparative schedule through Procurement, Director, Procurement, Accounts."""
    try:
        record = ComparativeSchedule.objects.get(pk=schedule_id)
    except ComparativeSchedule.DoesNotExist:
        return Response({"error": "Comparative schedule not found"}, status=status.HTTP_404_NOT_FOUND)

    employee = getattr(request.user, "employee_profile", None)
    role = (employee.role.name if employee and employee.role else "").upper()
    is_admin = request.user.is_superuser or role in {"ADMIN", "SYSTEM_ADMINISTRATOR"}
    stages = {
        "PENDING_DIRECTOR": ("director", {"DIRECTOR", "ZCHPC_DIRECTOR"}),
        "PENDING_PROCUREMENT": ("procurement_finalised", {"PROCUREMENT", "PROCUREMENT_OFFICER"}),
        "PENDING_ACCOUNTS": ("accounts", {"ACCOUNTS", "ACCOUNTANT", "FINANCE"}),
    }
    stage = stages.get(record.status)
    if stage is None:
        return Response({"error": "This schedule is no longer awaiting approval"}, status=status.HTTP_400_BAD_REQUEST)
    stage_name, allowed_roles = stage
    if not is_admin and not (role in allowed_roles or any(item in role for item in allowed_roles)):
        return Response({"error": "You are not authorized for this approval stage"}, status=status.HTTP_403_FORBIDDEN)
    setattr(record, f"{stage_name}_by_id", request.user.id)
    setattr(record, f"{stage_name}_at", timezone.now())
    record.status = {"director": "PENDING_PROCUREMENT", "procurement_finalised": "PENDING_ACCOUNTS", "accounts": "APPROVED"}[stage_name]
    record.save()
    return Response({"id": record.id, "schedule_number": record.schedule_number, "status": record.status})


# ============================
# Purchase Order Views
# ============================

@api_view(["GET"])
def purchase_order_list(request: Request) -> Response:
    """List purchase orders."""
    supplier_id = request.query_params.get("supplier_id")
    pending_delivery = (
        request.query_params.get("pending_delivery", "false").lower() == "true"
    )

    try:
        orders = _procurement_service.list_orders(
            supplier_id=int(supplier_id) if supplier_id else None,
            pending_delivery=pending_delivery
        )
        return Response(PurchaseOrderSerializer(orders, many=True).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["GET"])
def purchase_order_detail(request: Request, order_id: int) -> Response:
    """Get a purchase order."""
    try:
        order = _procurement_service.get_order(order_id)
        return Response(PurchaseOrderSerializer(order).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def purchase_order_send(request: Request, order_id: int) -> Response:
    """Send a purchase order to supplier."""
    try:
        order = _procurement_service.send_order_to_supplier(order_id)
        return Response(PurchaseOrderSerializer(order).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def purchase_order_receive(request: Request, order_id: int) -> Response:
    """Mark goods as received for an order."""
    serializer = MarkDeliveredSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = _procurement_service.mark_goods_received(
            order_id=order_id,
            is_partial=serializer.validated_data.get("is_partial", False)
        )
        return Response(PurchaseOrderSerializer(order).data)
    except Exception as e:
        return _handle_error(e)


@api_view(["POST"])
def purchase_order_cancel(request: Request, order_id: int) -> Response:
    """Cancel a purchase order."""
    serializer = CancelOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = _procurement_service.cancel_order(
            order_id=order_id,
            reason=serializer.validated_data.get("reason")
        )
        return Response(PurchaseOrderSerializer(order).data)
    except Exception as e:
        return _handle_error(e)
