export type FuelRequisitionStatus = 'PENDING_DEPARTMENT' | 'PENDING_RECIPIENT' | 'PENDING_FINANCE' | 'PENDING_DIRECTOR' | 'PENDING_ADMIN' | 'APPROVED' | 'REJECTED';

export interface FuelRequisition {
  id: number;
  requester_name: string;
  requester_email: string;
  requester_employee_id: string;
  department: string;
  programme: string;
  recipient_driver: string;
  requester_signature: string;
  vehicle_registration: string;
  request_date: string;
  diesel_quantity: string;
  diesel_quantity_words: string;
  petrol_quantity: string;
  petrol_quantity_words: string;
  finance_recommendation: string;
  purpose: string;
  destination: string;
  destination_dates: string;
  status: FuelRequisitionStatus;
  rejection_reason: string;
  rejected_by: string | null;
  rejected_at: string | null;
  rejected_at_stage: string;
  department_approved_by: string | null;
  department_approved_at: string | null;
  recipient_approved_by: string | null;
  recipient_approved_at: string | null;
  finance_approved_by: string | null;
  finance_approved_at: string | null;
  director_approved_by: string | null;
  director_approved_at: string | null;
  admin_approved_by: string | null;
  admin_approved_at: string | null;
  issuance_quantity: string | null;
  serial_numbers: string;
  issued_by_name: string;
  received_by_name: string;
  created_at: string;
}

export interface CreateFuelRequisitionData {
  programme?: string;
  recipient_driver: string;
  requester_signature?: string;
  vehicle_registration: string;
  request_date: string;
  diesel_quantity: number;
  diesel_quantity_words?: string;
  petrol_quantity: number;
  petrol_quantity_words?: string;
  purpose: string;
  destination: string;
  destination_dates?: string;
}
