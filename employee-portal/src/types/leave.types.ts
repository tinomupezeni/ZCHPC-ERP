export interface LeaveType {
  id: number;
  name: string;
  default_days_allowed: number;
}

export interface LeaveBalance {
  id: number;
  leave_type: number;
  leave_type_name: string;
  year: number;
  days_allowed: number;
  days_remaining: number;
  days_used: number;
  percentage_used: number;
}

export interface LeaveBalancesResponse {
  year: number;
  balances: LeaveBalance[];
  summary: {
    total_allowed: number;
    total_used: number;
    total_remaining: number;
  };
}

export type LeaveRequestStatus = 'Pending' | 'Approved' | 'Rejected' | 'Cancelled';

export interface LeaveRequest {
  id: number;
  leave_type: number;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  number_of_days: number;
  reason: string;
  status: LeaveRequestStatus;
  requested_on: string;
  reviewed_by_name: string | null;
  review_date: string | null;
  can_cancel: boolean;
}

export interface CreateLeaveRequestData {
  leave_type: number;
  start_date: string;
  end_date: string;
  reason?: string;
}

export interface LeaveRequestSummary {
  total_requests: number;
  pending_requests: number;
  approved_requests: number;
  rejected_requests: number;
  total_days_taken: number;
}

export interface LeaveCalendarEvent {
  id: number;
  title: string;
  start: string;
  end: string;
  status: LeaveRequestStatus;
  days: number;
}
