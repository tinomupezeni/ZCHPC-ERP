"""
Repository interfaces for the procurement module.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from modules.procurement.domain.entities import (
    Supplier,
    InventoryItem,
    BudgetCenter,
    PurchaseRequest,
    PurchaseOrder,
)
from modules.procurement.domain.value_objects import RequestStatus, OrderStatus


class ISupplierRepository(ABC):
    """Interface for supplier repository."""

    @abstractmethod
    def save(self, supplier: Supplier) -> Supplier:
        """Save a supplier."""
        ...

    @abstractmethod
    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Get a supplier by ID."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[Supplier]:
        """Get all suppliers."""
        ...

    @abstractmethod
    def get_active(self) -> List[Supplier]:
        """Get active suppliers."""
        ...

    @abstractmethod
    def search(self, query: str) -> List[Supplier]:
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
    def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        """Get an item by ID."""
        ...

    @abstractmethod
    def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        """Get an item by SKU."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[InventoryItem]:
        """Get all items."""
        ...

    @abstractmethod
    def get_low_stock(self) -> List[InventoryItem]:
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
    def get_by_id(self, budget_center_id: int) -> Optional[BudgetCenter]:
        """Get a budget center by ID."""
        ...

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[BudgetCenter]:
        """Get a budget center by code."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[BudgetCenter]:
        """Get all budget centers."""
        ...

    @abstractmethod
    def get_by_fiscal_year(self, year: int) -> List[BudgetCenter]:
        """Get budget centers for a fiscal year."""
        ...

    @abstractmethod
    def allocate_budget(
        self,
        budget_center_id: int,
        amount: Decimal
    ) -> BudgetCenter:
        """Allocate budget from a budget center."""
        ...

    @abstractmethod
    def release_budget(
        self,
        budget_center_id: int,
        amount: Decimal
    ) -> BudgetCenter:
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
        """Save a purchase request with its items."""
        ...

    @abstractmethod
    def get_by_id(self, request_id: int) -> Optional[PurchaseRequest]:
        """Get a request by ID with all items."""
        ...

    @abstractmethod
    def get_all(self) -> List[PurchaseRequest]:
        """Get all requests."""
        ...

    @abstractmethod
    def get_by_status(self, status: RequestStatus) -> List[PurchaseRequest]:
        """Get requests by status."""
        ...

    @abstractmethod
    def get_pending(self) -> List[PurchaseRequest]:
        """Get pending requests."""
        ...

    @abstractmethod
    def get_pending_level1(self) -> List[PurchaseRequest]:
        """Get requests pending Level 1 approval."""
        ...

    @abstractmethod
    def get_pending_level2(self) -> List[PurchaseRequest]:
        """Get requests pending Level 2 approval."""
        ...

    @abstractmethod
    def get_by_requester(self, requester_id: int) -> List[PurchaseRequest]:
        """Get requests by requester."""
        ...

    @abstractmethod
    def get_by_budget_center(
        self,
        budget_center_id: int
    ) -> List[PurchaseRequest]:
        """Get requests by budget center."""
        ...

    @abstractmethod
    def update_status(
        self,
        request_id: int,
        status: RequestStatus
    ) -> PurchaseRequest:
        """Update request status."""
        ...

    @abstractmethod
    def delete(self, request_id: int) -> bool:
        """Delete a request (only if pending)."""
        ...


class IPurchaseOrderRepository(ABC):
    """Interface for purchase order repository."""

    @abstractmethod
    def save(self, order: PurchaseOrder) -> PurchaseOrder:
        """Save a purchase order."""
        ...

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        """Get an order by ID."""
        ...

    @abstractmethod
    def get_by_order_number(self, order_number: str) -> Optional[PurchaseOrder]:
        """Get an order by order number."""
        ...

    @abstractmethod
    def get_by_request_id(self, request_id: int) -> Optional[PurchaseOrder]:
        """Get order by request ID."""
        ...

    @abstractmethod
    def get_all(self) -> List[PurchaseOrder]:
        """Get all orders."""
        ...

    @abstractmethod
    def get_by_status(self, status: OrderStatus) -> List[PurchaseOrder]:
        """Get orders by status."""
        ...

    @abstractmethod
    def get_by_supplier(self, supplier_id: int) -> List[PurchaseOrder]:
        """Get orders by supplier."""
        ...

    @abstractmethod
    def get_pending_delivery(self) -> List[PurchaseOrder]:
        """Get orders pending delivery."""
        ...

    @abstractmethod
    def delete(self, order_id: int) -> bool:
        """Delete an order (only if draft)."""
        ...
