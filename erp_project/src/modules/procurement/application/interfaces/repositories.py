"""
Repository interfaces for the procurement module.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from modules.procurement.domain.entities import (
    BudgetCenter,
    InventoryItem,
    PurchaseOrder,
    PurchaseRequest,
    PurchaseRequestCategory,
    Supplier,
)
from modules.procurement.domain.value_objects import OrderStatus, RequestStatus


class ISupplierRepository(ABC):
    """Interface for supplier repository."""

    @abstractmethod
    def save(self, supplier: Supplier) -> Supplier:
        """Save a supplier."""
        ...

    @abstractmethod
    def get_by_id(self, supplier_id: int) -> Supplier | None:
        """Get a supplier by ID."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> list[Supplier]:
        """Get all suppliers."""
        ...

    @abstractmethod
    def get_active(self) -> list[Supplier]:
        """Get active suppliers."""
        ...

    @abstractmethod
    def search(self, query: str) -> list[Supplier]:
        """Search suppliers by name."""
        ...

    @abstractmethod
    def delete(self, supplier_id: int) -> bool:
        """Delete a supplier."""
        ...


class IInventoryItemRepository(ABC):
    """Interface for inventory item repository."""

    @abstractmethod
    def save(self, item: InventoryItem) -> InventoryItem:
        """Save an inventory item."""
        ...

    @abstractmethod
    def get_by_id(self, item_id: int) -> InventoryItem | None:
        """Get an item by ID."""
        ...

    @abstractmethod
    def get_by_sku(self, sku: str) -> InventoryItem | None:
        """Get an item by SKU."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> list[InventoryItem]:
        """Get all items."""
        ...

    @abstractmethod
    def get_low_stock(self) -> list[InventoryItem]:
        """Get items that need reordering."""
        ...

    @abstractmethod
    def delete(self, item_id: int) -> bool:
        """Delete an item."""
        ...


class IBudgetCenterRepository(ABC):
    """Interface for budget center repository."""

    @abstractmethod
    def save(self, budget_center: BudgetCenter) -> BudgetCenter:
        """Save a budget center."""
        ...

    @abstractmethod
    def get_by_id(self, budget_center_id: int) -> BudgetCenter | None:
        """Get a budget center by ID."""
        ...

    @abstractmethod
    def get_by_code(self, code: str) -> BudgetCenter | None:
        """Get a budget center by code."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> list[BudgetCenter]:
        """Get all budget centers."""
        ...

    @abstractmethod
    def get_by_fiscal_year(self, year: int) -> list[BudgetCenter]:
        """Get budget centers for a fiscal year."""
        ...

    @abstractmethod
    def allocate_budget(self, budget_center_id: int, amount: Decimal) -> BudgetCenter:
        """Allocate budget from a budget center."""
        ...

    @abstractmethod
    def release_budget(self, budget_center_id: int, amount: Decimal) -> BudgetCenter:
        """Release allocated budget back to budget center."""
        ...

    @abstractmethod
    def delete(self, budget_center_id: int) -> bool:
        """Delete a budget center."""
        ...


class IPurchaseRequestRepository(ABC):
    """Interface for purchase request repository."""

    @abstractmethod
    def save(self, request: PurchaseRequest) -> PurchaseRequest:
        """Save a purchase request with its items and decisions."""
        ...

    @abstractmethod
    def get_by_id(self, request_id: int) -> PurchaseRequest | None:
        """Get a request by ID with all items and decisions."""
        ...

    @abstractmethod
    def get_all(self) -> list[PurchaseRequest]:
        """Get all requests."""
        ...

    @abstractmethod
    def get_by_status(self, status: RequestStatus) -> list[PurchaseRequest]:
        """Get requests by status."""
        ...

    @abstractmethod
    def get_pending_department_head(self) -> list[PurchaseRequest]:
        """Get requests pending Department Head approval."""
        ...

    @abstractmethod
    def get_pending_accounts(self) -> list[PurchaseRequest]:
        """Get requests pending Accounts verification."""
        ...

    @abstractmethod
    def get_pending_gm(self) -> list[PurchaseRequest]:
        """Get requests pending GM recommendation."""
        ...

    @abstractmethod
    def get_pending_director(self) -> list[PurchaseRequest]:
        """Get requests pending Director approval."""
        ...

    @abstractmethod
    def get_pending_procurement(self) -> list[PurchaseRequest]:
        """Get requests pending Procurement processing."""
        ...

    @abstractmethod
    def get_by_requester(self, requester_id: int) -> list[PurchaseRequest]:
        """Get requests by requester."""
        ...

    @abstractmethod
    def delete(self, request_id: int) -> bool:
        """Delete a request (only if pending/draft)."""
        ...


class IPurchaseRequestCategoryRepository(ABC):
    """
    Interface for the employee-facing Purchase Request category lookup
    (Slice F11-A). Read-only by design - creating/deactivating categories is
    a Finance-curation activity outside this slice's scope, not an employee
    or requester-facing operation.
    """

    @abstractmethod
    def get_by_id(self, category_id: int) -> PurchaseRequestCategory | None:
        """Get a category by ID, active or not - callers decide what to do with an inactive one."""
        ...

    @abstractmethod
    def get_all_active(self) -> list[PurchaseRequestCategory]:
        """Get every category currently selectable by an employee."""
        ...


class IPurchaseOrderRepository(ABC):
    """Interface for purchase order repository."""

    @abstractmethod
    def save(self, order: PurchaseOrder) -> PurchaseOrder:
        """Save a purchase order."""
        ...

    @abstractmethod
    def get_by_id(self, order_id: int) -> PurchaseOrder | None:
        """Get an order by ID."""
        ...

    @abstractmethod
    def get_by_order_number(self, order_number: str) -> PurchaseOrder | None:
        """Get an order by order number."""
        ...

    @abstractmethod
    def get_by_request_id(self, request_id: int) -> PurchaseOrder | None:
        """Get order by request ID."""
        ...

    @abstractmethod
    def get_all(self) -> list[PurchaseOrder]:
        """Get all orders."""
        ...

    @abstractmethod
    def get_by_status(self, status: OrderStatus) -> list[PurchaseOrder]:
        """Get orders by status."""
        ...

    @abstractmethod
    def get_by_supplier(self, supplier_id: int) -> list[PurchaseOrder]:
        """Get orders by supplier."""
        ...

    @abstractmethod
    def get_pending_delivery(self) -> list[PurchaseOrder]:
        """Get orders pending delivery."""
        ...

    @abstractmethod
    def delete(self, order_id: int) -> bool:
        """Delete an order (only if draft)."""
        ...
