"""
Purchase Request Application Use Cases.

These classes orchestrate the business workflow for purchase requests
by delegating domain rules to the aggregate root and persisting
changes via the repository.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List

from shared.domain.exceptions import NotFoundError
from modules.procurement.domain.entities import PurchaseRequest, PurchaseRequestItem
from modules.procurement.application.interfaces import IPurchaseRequestRepository


@dataclass
class PurchaseRequestItemDTO:
    """DTO for creating a purchase request item."""

    description: str
    quantity: int
    expected_delivery_period: str
    estimated_cost: Decimal
    budget_code_id: int


@dataclass
class CreatePurchaseRequestDTO:
    """DTO for creating a purchase request."""

    requester_id: int
    requester_name: str
    department_id: int
    department_name: str
    designation: str
    contact: str
    items: List[PurchaseRequestItemDTO] = field(default_factory=list)


class CreatePurchaseRequest:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, dto: CreatePurchaseRequestDTO) -> PurchaseRequest:
        request = PurchaseRequest.create(
            requester_id=dto.requester_id,
            requester_name=dto.requester_name,
            department_id=dto.department_id,
            department_name=dto.department_name,
            designation=dto.designation,
            contact=dto.contact,
        )

        for item_dto in dto.items:
            item = PurchaseRequestItem(
                description=item_dto.description,
                quantity=item_dto.quantity,
                expected_delivery_period=item_dto.expected_delivery_period,
                estimated_cost=item_dto.estimated_cost,
                budget_code_id=item_dto.budget_code_id,
            )
            request.add_item(item)

        return self.repository.save(request)


class SubmitPurchaseRequest:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, request_id: int) -> PurchaseRequest:
        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        request.submit()
        return self.repository.save(request)


class ApprovePurchaseRequestByDepartmentHead:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, request_id: int, actor_id: int) -> PurchaseRequest:
        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        request.approve_by_department_head(actor_id)
        return self.repository.save(request)


class VerifyPurchaseRequestByAccounts:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, request_id: int, actor_id: int) -> PurchaseRequest:
        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        request.verify_by_accounts(actor_id)
        return self.repository.save(request)


class RecommendPurchaseRequestByGM:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, request_id: int, actor_id: int) -> PurchaseRequest:
        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        request.recommend_by_gm(actor_id)
        return self.repository.save(request)


class ApprovePurchaseRequestByDirector:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, request_id: int, actor_id: int) -> PurchaseRequest:
        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        request.approve_by_director(actor_id)
        return self.repository.save(request)


class ProcessPurchaseRequestByProcurement:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, request_id: int, actor_id: int) -> PurchaseRequest:
        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        request.process_by_procurement(actor_id)
        return self.repository.save(request)


class RejectPurchaseRequest:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, request_id: int, actor_id: int, reason: str) -> PurchaseRequest:
        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        request.reject(actor_id, reason)
        return self.repository.save(request)


class CorrectAndResubmitPurchaseRequest:
    def __init__(self, repository: IPurchaseRequestRepository) -> None:
        self.repository = repository

    def execute(self, request_id: int) -> PurchaseRequest:
        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        request.correct_and_resubmit()
        return self.repository.save(request)
