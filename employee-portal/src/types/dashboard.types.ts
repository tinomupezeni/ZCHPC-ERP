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

export interface DashboardSummary {
  employee_name: string;
  employee_id: string;
  position: string | null;
  department: string | null;
  total_leave_balance: number;
  leave_balances: LeaveBalance[];
  pending_leave_requests: number;
  pending_expense_claims: number;
  open_tickets: number;
  attendance_this_month: number;
  today_status: 'clocked_in' | 'clocked_out' | 'not_clocked';
  recent_attendance: AttendanceSummary[];
  upcoming_events: UpcomingEvent[];
  unread_notifications: number;
}

export interface Notification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
  related_object_type: string | null;
  related_object_id: number | null;
}
