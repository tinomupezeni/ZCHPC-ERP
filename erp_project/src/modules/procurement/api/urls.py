"""
URL patterns for the procurement module API.
"""

from django.urls import path

from modules.procurement.api import purchase_request_views, views

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

    # Purchase Request Categories (Slice F11-A - employee-facing lookup)
    path(
        "purchase-request-categories/",
        purchase_request_views.purchase_request_categories_list,
        name="purchase-request-category-list"
    ),

    # Purchase Requests (redesigned workflow)
    path(
        "requests/",
        purchase_request_views.purchase_request_list,
        name="request-list"
    ),
    path(
        "requests/<int:request_id>/",
        purchase_request_views.purchase_request_detail,
        name="request-detail"
    ),
    path(
        "requests/<int:request_id>/submit/",
        purchase_request_views.purchase_request_submit,
        name="request-submit"
    ),
    path(
        "requests/<int:request_id>/department-head/approve/",
        purchase_request_views.purchase_request_department_head_approve,
        name="request-department-head-approve"
    ),
    path(
        "requests/<int:request_id>/accounts/verify/",
        purchase_request_views.purchase_request_accounts_verify,
        name="request-accounts-verify"
    ),
    path(
        "requests/<int:request_id>/gm/recommend/",
        purchase_request_views.purchase_request_gm_recommend,
        name="request-gm-recommend"
    ),
    path(
        "requests/<int:request_id>/director/approve/",
        purchase_request_views.purchase_request_director_approve,
        name="request-director-approve"
    ),
    path(
        "requests/<int:request_id>/reject/",
        purchase_request_views.purchase_request_reject,
        name="request-reject"
    ),
    path(
        "requests/<int:request_id>/correct-and-resubmit/",
        purchase_request_views.purchase_request_correct_and_resubmit,
        name="request-correct-and-resubmit"
    ),
    path(
        "requests/<int:request_id>/process/",
        purchase_request_views.purchase_request_process,
        name="request-process"
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
