export type StoresRequisitionStatus = 'PENDING_DEPARTMENT' | 'PENDING_PROCUREMENT' | 'PENDING_ACCOUNTS' | 'PENDING_GENERAL_MANAGER' | 'PENDING_DIRECTOR' | 'PENDING_ADMIN' | 'APPROVED' | 'REJECTED';

export interface StoresItem {
  description: string;
  quantity_required: string;
  budget_code: string;
  required_by: string;
}

export interface StoresRequisition {
  id: number;
  requisition_number: string;
  department: string;
  items: StoresItem[];
  status: StoresRequisitionStatus;
  rejection_reason: string;
  created_at: string;
}

export interface CreateStoresRequisitionData {
  items: StoresItem[];
}
