"""
URL patterns for the procurement module API.
"""

from django.urls import path

from modules.procurement.api import views

app_name = "procurement_v2"

urlpatterns = [
    # Suppliers
    path(
        "suppliers/",
        views.supplier_list,
        name="supplier-list"
    ),
    path(
        "suppliers/<int:supplier_id>/",
        views.supplier_detail,
        name="supplier-detail"
    ),
    path(
        "suppliers/<int:supplier_id>/activate/",
        views.supplier_activate,
        name="supplier-activate"
    ),

    # Inventory Items
    path(
        "inventory/",
        views.inventory_item_list,
        name="inventory-list"
    ),
    path(
        "inventory/<int:item_id>/",
        views.inventory_item_detail,
        name="inventory-detail"
    ),

    # Budget Centers
    path(
        "budget-centers/",
        views.budget_center_list,
        name="budget-center-list"
    ),
    path(
        "budget-centers/<int:center_id>/",
        views.budget_center_detail,
        name="budget-center-detail"
    ),

    # Purchase Requests
    path(
        "requests/",
        views.purchase_request_list,
        name="request-list"
    ),
    path(
        "requests/<int:request_id>/",
        views.purchase_request_detail,
        name="request-detail"
    ),
    path(
        "requests/<int:request_id>/approve-level1/",
        views.purchase_request_approve_level1,
        name="request-approve-level1"
    ),
    path(
        "requests/<int:request_id>/approve-level2/",
        views.purchase_request_approve_level2,
        name="request-approve-level2"
    ),
    path(
        "requests/<int:request_id>/reject/",
        views.purchase_request_reject,
        name="request-reject"
    ),
    path(
        "fuel-requisitions/<int:requisition_id>/approve/",
        views.fuel_requisition_approve,
        name="fuel-requisition-approve"
    ),
    path(
        "stores-requisitions/<int:requisition_id>/approve/",
        views.stores_requisition_approve,
        name="stores-requisition-approve"
    ),
    path(
        "comparative-schedules/<int:schedule_id>/approve/",
        views.comparative_schedule_approve,
        name="comparative-schedule-approve"
    ),

    # Purchase Orders
    path(
        "orders/",
        views.purchase_order_list,
        name="order-list"
    ),
    path(
        "orders/<int:order_id>/",
        views.purchase_order_detail,
        name="order-detail"
    ),
    path(
        "orders/<int:order_id>/send/",
        views.purchase_order_send,
        name="order-send"
    ),
    path(
        "orders/<int:order_id>/receive/",
        views.purchase_order_receive,
        name="order-receive"
    ),
    path(
        "orders/<int:order_id>/cancel/",
        views.purchase_order_cancel,
        name="order-cancel"
    ),
]
