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

export interface PurchaseRequestItem {
  id: number;
  description: string;
  quantity: number;
  expected_delivery_period: string;
  estimated_cost: string;
  budget_code_id: number;
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
