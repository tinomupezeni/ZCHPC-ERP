export interface LeaveBalance {
  leave_type: string;
  leave_type_id: number;
  total_days: number;
  used_days: number;
  pending_days: number;
  available_days: number;
}

export interface AttendanceSummary {
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  status: 'present' | 'absent' | 'late' | 'leave';
}

export interface UpcomingEvent {
  id: number;
  title: string;
  event_type: string;
  start_date: string;
  end_date: string;
  description: string;
  is_all_day: boolean;
}

/** GET /portal/dashboard/ - field names as DashboardSerializer sends them. */
export interface DashboardSummary {
  employee_name: string;
  employee_id: string;
  position_name: string | null;
  department_name: string | null;
  leave_balances: LeaveBalance[];
  /** The user's own pending leave requests. */
  pending_leave_requests: number;
  /** Pending requests waiting for this user's review (0 without the review capability). */
  leave_requests_to_review: number;
  pending_expense_claims: number;
  open_tickets: number;
  /** Days present this month (read as attendance_this_month before, which the API never sends). */
  monthly_attendance_count: number;
  recent_attendance: AttendanceSummary[];
  upcoming_events: UpcomingEvent[];
  unread_notifications: number;
}
