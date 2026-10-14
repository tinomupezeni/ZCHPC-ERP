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
  requester_name: string;
  requester_email: string;
  requester_employee_id: string;
  department: string;
  items: StoresItem[];
  status: StoresRequisitionStatus;
  rejection_reason: string;
  rejected_by: string | null;
  rejected_at: string | null;
  rejected_at_stage: string;
  department_approved_by: string | null;
  department_approved_at: string | null;
  procurement_approved_by: string | null;
  procurement_approved_at: string | null;
  accounts_approved_by: string | null;
  accounts_approved_at: string | null;
  general_manager_approved_by: string | null;
  general_manager_approved_at: string | null;
  director_approved_by: string | null;
  director_approved_at: string | null;
  admin_approved_by: string | null;
  admin_approved_at: string | null;
  created_at: string;
}

export interface CreateStoresRequisitionData {
  items: StoresItem[];
}
