export interface AttendanceRecord {
  id: number;
  employee: number;
  employee_name: string;
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  notes: string;
  status: 'complete' | 'clocked_in' | 'absent';
}

export interface AttendanceStatus {
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  status: 'not_clocked' | 'clocked_in' | 'clocked_out';
  hours_worked: number | null;
}

export interface AttendanceSummary {
  month: number;
  year: number;
  total_working_days: number;
  days_present: number;
  days_absent: number;
  days_late: number;
  days_on_leave: number;
  total_hours_worked: number;
  average_clock_in: string | null;
  average_clock_out: string | null;
}

export interface AttendanceHistory {
  records: AttendanceRecord[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface ClockResponse {
  action: 'clock_in' | 'clock_out';
  message: string;
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  hours_worked: number | null;
}
