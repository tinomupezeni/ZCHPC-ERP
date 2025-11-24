from ..entities.purchase_request import PurchaseRequest

class PurchaseRequestRepository:

    @staticmethod
    def get_all():
        return PurchaseRequest.objects.all()

    @staticmethod
    def get_pending():
        return PurchaseRequest.objects.filter(status='PENDING')

    @staticmethod
    def get_by_id(request_id):
        return PurchaseRequest.objects.get(id=request_id)

    @staticmethod
    def create(**kwargs):
        return PurchaseRequest.objects.create(**kwargs)

    @staticmethod
    def update_status(request_id, status):
        pr = PurchaseRequest.objects.get(id=request_id)
        pr.status = status
        pr.save()
        return pr
