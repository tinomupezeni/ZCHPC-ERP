from ..repositories.purchase_request_repository import PurchaseRequestRepository
from ..repositories.vendor_repository import VendorRepository
from ..entities.purchase_order import PurchaseOrder
from django.utils.crypto import get_random_string

class ProcurementService:

    @staticmethod
    def create_purchase_request(requester, vendor_id, items):
        vendor = VendorRepository.get_by_id(vendor_id)
        pr = PurchaseRequestRepository.create(requester=requester, vendor=vendor)
        
        total_amount = 0
        for item in items:
            pr.items.add(item['item'], through_defaults={'quantity': item['quantity']})
            total_amount += item['quantity'] * item['item'].price_per_unit
        
        pr.total_amount = total_amount
        pr.save()
        return pr

    @staticmethod
    def approve_purchase_request(request_id):
        pr = PurchaseRequestRepository.update_status(request_id, 'APPROVED')
        po = PurchaseOrder.objects.create(
            purchase_request=pr,
            order_number=f"PO-{get_random_string(8).upper()}"
        )
        return po
