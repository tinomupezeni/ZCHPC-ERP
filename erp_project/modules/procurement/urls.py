from django.urls import path
from .views.purchase_request_view import PurchaseRequestView, PurchaseRequestApprovalView

urlpatterns = [
    path('purchase-requests/', PurchaseRequestView.as_view(), name='purchase_requests'),
    path('purchase-requests/<int:pk>/approve/', PurchaseRequestApprovalView.as_view(), name='approve_purchase_request'),
]
