from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.procurement_service import ProcurementService
from ..services.approval_service import ApprovalService
from ..serializers.purchase_request_serializer import PurchaseRequestSerializer
from ..repositories.purchase_request_repository import PurchaseRequestRepository

class PurchaseRequestView(APIView):

    def get(self, request):
        prs = PurchaseRequestRepository.get_all()
        serializer = PurchaseRequestSerializer(prs, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        pr = ProcurementService.create_purchase_request(
            requester=data['requester'],
            vendor_id=data['vendor_id'],
            budget_center_id=data['budget_center_id'],
            items=data['items']
        )
        serializer = PurchaseRequestSerializer(pr)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PurchaseRequestApprovalView(APIView):

    def post(self, request, pk, level):
        try:
            if level == 1:
                pr = ApprovalService.level1_approve(pk)
                return Response({"status": pr.status}, status=status.HTTP_200_OK)
            elif level == 2:
                po = ApprovalService.level2_approve(pk)
                return Response({"order_number": po.order_number}, status=status.HTTP_200_OK)
            elif level == "reject":
                pr = ApprovalService.reject(pk)
                return Response({"status": pr.status}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
