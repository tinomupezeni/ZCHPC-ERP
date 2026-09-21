import pytest
from decimal import Decimal
from datetime import datetime
from django.test import TestCase

from modules.procurement.domain.entities import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestDecision,
)
from modules.procurement.domain.value_objects import (
    RequestStatus,
    DecisionStage,
    DecisionType,
)
from modules.procurement.infrastructure.persistence.django_purchase_request_repository import (
    DjangoPurchaseRequestRepository,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
)
from modules.hr.infrastructure.persistence.models import Employees, Department
from django.contrib.auth import get_user_model
from modules.accounts.infrastructure.persistence.models import AccountChart

User = get_user_model()


@pytest.mark.django_db
class TestDjangoPurchaseRequestRepository(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="pwd"
        )
        self.department = Department.objects.create(name="IT Department")
        self.employee = Employees.objects.create(
            user=self.user,
            first_name="John",
            surname="Doe",
            department=self.department,
            employee_id="EMP001",
        )
        self.account = AccountChart.objects.create(
            code="1001", name="Hardware", account_type="EXPENSE"
        )

        self.repo = DjangoPurchaseRequestRepository()

    def test_save_and_get_purchase_request(self):
        # Create a domain PurchaseRequest
        request = PurchaseRequest.create(
            requester_id=self.employee.id,
            requester_name="John Doe",
            department_id=self.department.id,
            department_name="IT Department",
            designation="Developer",
            contact="ext 123",
        )
        request.add_item(
            PurchaseRequestItem(
                description="Laptop",
                quantity=2,
                expected_delivery_period="1 week",
                estimated_cost=Decimal("2000.00"),
                budget_code_id=self.account.id,
            )
        )

        # Save
        saved_req = self.repo.save(request)

        assert saved_req.id is not None
        assert saved_req.requisition_number.startswith("PR-")

        # Retrieve
        fetched_req = self.repo.get_by_id(saved_req.id)
        assert fetched_req is not None
        assert fetched_req.requester_id == self.employee.id
        assert fetched_req.department_name == "IT Department"
        assert fetched_req.status == RequestStatus.DRAFT

        assert len(fetched_req.items) == 1
        assert fetched_req.items[0].description == "Laptop"
        assert fetched_req.items[0].estimated_cost == Decimal("2000.00")

        # Check that no Vendor or InventoryItem is required/linked
        model_instance = PurchaseRequestModel.objects.get(id=saved_req.id)
        assert hasattr(model_instance, "vendor") is False
        assert hasattr(model_instance, "budget_center") is False

    def test_decision_history_is_preserved(self):
        # Create and save a DRAFT
        request = PurchaseRequest.create(
            requester_id=self.employee.id,
            requester_name="John Doe",
            department_id=self.department.id,
            department_name="IT Department",
            designation="Developer",
            contact="ext 123",
        )
        request.add_item(
            PurchaseRequestItem(
                description="Laptop",
                quantity=2,
                expected_delivery_period="1 week",
                estimated_cost=Decimal("2000.00"),
                budget_code_id=self.account.id,
            )
        )
        saved_req = self.repo.save(request)

        # Simulate state transitions
        saved_req.submit()
        saved_req.approve_by_department_head(self.employee.id)
        saved_req = self.repo.save(saved_req)

        assert len(saved_req.decisions) == 1
        assert saved_req.decisions[0].stage == DecisionStage.DEPARTMENT_HEAD

        # Fetch again to ensure persistence
        fetched_req = self.repo.get_by_id(saved_req.id)
        assert len(fetched_req.decisions) == 1

        # Further transition
        fetched_req.verify_by_accounts(self.employee.id)
        fetched_req = self.repo.save(fetched_req)

        assert len(fetched_req.decisions) == 2
        assert fetched_req.decisions[1].stage == DecisionStage.ACCOUNTS
        assert fetched_req.decisions[1].decision == DecisionType.VERIFIED

    def _fully_approved_request(self):
        request = PurchaseRequest.create(
            requester_id=self.employee.id,
            requester_name="John Doe",
            department_id=self.department.id,
            department_name="IT Department",
            designation="Developer",
            contact="ext 123",
        )
        request.add_item(
            PurchaseRequestItem(
                description="Laptop",
                quantity=2,
                expected_delivery_period="1 week",
                estimated_cost=Decimal("2000.00"),
                budget_code_id=self.account.id,
            )
        )
        request = self.repo.save(request)
        request.submit()
        request.approve_by_department_head(self.employee.id)
        request.verify_by_accounts(self.employee.id)
        request.recommend_by_gm(self.employee.id)
        request.approve_by_director(self.employee.id)
        return self.repo.save(request)

    def test_purchase_order_number_round_trips_through_processing(self):
        """F23: process_by_procurement's PO number survives save + reload."""
        request = self._fully_approved_request()

        request.process_by_procurement(self.employee.id, "PO-REPO-001")
        saved = self.repo.save(request)

        assert saved.purchase_order_number == "PO-REPO-001"

        fetched = self.repo.get_by_id(saved.id)
        assert fetched.purchase_order_number == "PO-REPO-001"
        assert fetched.status == RequestStatus.PROCESSED

    def test_exists_by_purchase_order_number(self):
        """F23: the uniqueness pre-check ProcessPurchaseRequestByProcurement relies on."""
        assert self.repo.exists_by_purchase_order_number("PO-REPO-002") is False

        request = self._fully_approved_request()
        request.process_by_procurement(self.employee.id, "PO-REPO-002")
        self.repo.save(request)

        assert self.repo.exists_by_purchase_order_number("PO-REPO-002") is True
        assert self.repo.exists_by_purchase_order_number("PO-REPO-999") is False

    def test_unprocessed_requests_have_no_purchase_order_number(self):
        request = PurchaseRequest.create(
            requester_id=self.employee.id,
            requester_name="John Doe",
            department_id=self.department.id,
            department_name="IT Department",
            designation="Developer",
            contact="ext 123",
        )
        saved = self.repo.save(request)

        assert saved.purchase_order_number is None
        assert self.repo.get_by_id(saved.id).purchase_order_number is None
