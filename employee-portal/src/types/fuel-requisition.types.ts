export type FuelRequisitionStatus = 'PENDING_DEPARTMENT' | 'PENDING_RECIPIENT' | 'PENDING_FINANCE' | 'PENDING_DIRECTOR' | 'PENDING_ADMIN' | 'APPROVED' | 'REJECTED';

export interface FuelRequisition {
  id: number;
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
  purpose: string;
  destination: string;
  destination_dates: string;
  status: FuelRequisitionStatus;
  rejection_reason: string;
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
