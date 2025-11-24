from ..repositories.purchase_request_repository import PurchaseRequestRepository
from ..repositories.budget_repository import BudgetRepository
from ..entities.purchase_order import PurchaseOrder
from django.utils.crypto import get_random_string

class ApprovalService:

    @staticmethod
    def level1_approve(request_id):
        pr = PurchaseRequestRepository.get_by_id(request_id)
        # Check budget
        if not BudgetRepository.check_budget(pr.budget_center.id, pr.total_amount):
            raise Exception("Budget exceeded for this request")
        # Update status
        pr = PurchaseRequestRepository.update_status(request_id, 'LEVEL1_APPROVED')
        return pr

    @staticmethod
    def level2_approve(request_id):
        pr = PurchaseRequestRepository.get_by_id(request_id)
        # Allocate budget
        BudgetRepository.allocate_budget(pr.budget_center.id, pr.total_amount)
        # Update status
        pr = PurchaseRequestRepository.update_status(request_id, 'LEVEL2_APPROVED')
        # Create purchase order
        po = PurchaseOrder.objects.create(
            purchase_request=pr,
            order_number=f"PO-{get_random_string(8).upper()}"
        )
        return po

    @staticmethod
    def reject(request_id):
        pr = PurchaseRequestRepository.update_status(request_id, 'REJECTED')
        return pr
