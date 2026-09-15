export type PurchaseRequestStatus =
  | 'DRAFT'
  | 'PENDING_DEPARTMENT_HEAD'
  | 'PENDING_ACCOUNTS'
  | 'PENDING_GM'
  | 'PENDING_DIRECTOR'
  | 'PENDING_PROCUREMENT'
  | 'PROCESSED'
  | 'REJECTED';

export type PurchaseRequestDecisionStage = 'DEPARTMENT_HEAD' | 'ACCOUNTS' | 'GM' | 'DIRECTOR';

export type PurchaseRequestDecisionType = 'APPROVED' | 'VERIFIED' | 'RECOMMENDED' | 'REJECTED';

export interface PurchaseRequestCategory {
  id: number;
  name: string;
}

/**
 * The category an item's budget_code_id resolves back to (Slice 2), for
 * pre-filling an edit form. Never the GL code itself - id/name are the same
 * disclosure boundary as PurchaseRequestCategory; is_active tells the
 * frontend whether this is still a legal fresh choice or historical-only.
 */
export interface PurchaseRequestItemCategory {
  id: number;
  name: string;
  is_active: boolean;
}

export interface PurchaseRequestItem {
  id: number;
  description: string;
  quantity: number;
  expected_delivery_period: string;
  estimated_cost: string;
  budget_code_id: number;
  category: PurchaseRequestItemCategory | null;
}

export interface PurchaseRequestDecision {
  id: number;
  stage: PurchaseRequestDecisionStage;
  decision: PurchaseRequestDecisionType;
  actor_id: number;
  reason: string;
  created_at: string;
}

export interface PurchaseRequest {
  id: number;
  requisition_number: string;
  requester_id: number;
  requester_name: string;
  department_id: number;
  department_name: string;
  designation: string;
  contact: string;
  status: PurchaseRequestStatus;
  total_estimated_cost: string;
  items: PurchaseRequestItem[];
  decisions: PurchaseRequestDecision[];
  processed_by: number | null;
  processed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PurchaseRequestListItem {
  id: number;
  requisition_number: string;
  requester_id: number;
  requester_name: string;
  department_id: number;
  department_name: string;
  status: PurchaseRequestStatus;
  total_estimated_cost: string;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * Employee Portal creation input. Deliberately has no budget_code_id - the
 * employee only ever picks a category; the server resolves the GL code
 * (see modules.procurement F11-A on the backend).
 */
export interface CreatePurchaseRequestItemData {
  description: string;
  quantity: number;
  expected_delivery_period: string;
  estimated_cost: string;
  category_id: number;
}

export interface CreatePurchaseRequestData {
  items: CreatePurchaseRequestItemData[];
}

/**
 * Slice 2: editing a DRAFT, or correcting a REJECTED request (the backend
 * transitions REJECTED -> DRAFT as part of the same save - see
 * UpdatePurchaseRequestItems). `id` identifies an existing item to update;
 * omit it to add a new item. Still no budget_code_id - this endpoint is
 * exclusively the employee-facing category path.
 */
export interface UpdatePurchaseRequestItemData {
  id?: number;
  description: string;
  quantity: number;
  expected_delivery_period: string;
  estimated_cost: string;
  category_id: number;
}

export interface UpdatePurchaseRequestData {
  items: UpdatePurchaseRequestItemData[];
}
