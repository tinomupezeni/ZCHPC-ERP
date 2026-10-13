import api from './api';
import axios from 'axios';
import { format, parseISO } from 'date-fns';
import type {
  AttendanceStatus,
  AttendanceSummary,
  AttendanceHistory,
  AttendanceRecord,
  ClockResponse,
} from '@/types/attendance.types';

// What /portal/attendance/* actually returns (portal/api/serializers.py). The
// page's types use other names, so every response is mapped here.
interface ApiClockStatus {
  is_clocked_in: boolean;
  clock_in_time: string | null;
  clock_out_time: string | null;
  worked_hours: number | null;
}

interface ApiAttendanceRecord {
  id: number;
  date: string;
  time_in: string | null;
  time_out: string | null;
  status: string;
}

interface ApiAttendanceSummary {
  month: number;
  year: number;
  total_days: number;
  present_days: number;
  absent_days: number;
  leave_days: number;
  late_days: number;
  total_hours: number;
}

/** ISO datetime from the API -> local "HH:mm", the form the components show. */
function toClockTime(value: string | null): string | null {
  return value ? format(parseISO(value), 'HH:mm') : null;
}

export function toAttendanceStatus(data: ApiClockStatus): AttendanceStatus {
  let status: AttendanceStatus['status'] = 'not_clocked';
  if (data.is_clocked_in) status = 'clocked_in';
  else if (data.clock_out_time) status = 'clocked_out';
  return {
    date: format(new Date(), 'yyyy-MM-dd'),
    clock_in: toClockTime(data.clock_in_time),
    clock_out: toClockTime(data.clock_out_time),
    status,
    hours_worked: data.worked_hours,
  };
}

function toAttendanceRecord(data: ApiAttendanceRecord): AttendanceRecord {
  let status: AttendanceRecord['status'] = 'absent';
  if (data.time_in && data.time_out) status = 'complete';
  else if (data.time_in) status = 'clocked_in';
  return {
    id: data.id,
    employee: 0,
    employee_name: '',
    date: data.date,
    clock_in: toClockTime(data.time_in),
    clock_out: toClockTime(data.time_out),
    notes: '',
    status,
  };
}

/** The API returns a plain list, newest first, and does not paginate. */
export function toAttendanceHistory(
  data: ApiAttendanceRecord[],
  pageSize?: number
): AttendanceHistory {
  const all = Array.isArray(data) ? data : [];
  const shown = pageSize ? all.slice(0, pageSize) : all;
  return {
    records: shown.map(toAttendanceRecord),
    total_count: all.length,
    page: 1,
    page_size: pageSize ?? all.length,
  };
}

export function toAttendanceSummary(data: ApiAttendanceSummary): AttendanceSummary {
  return {
    month: data.month,
    year: data.year,
    total_working_days: data.total_days,
    days_present: data.present_days,
    days_absent: data.absent_days,
    days_late: data.late_days,
    days_on_leave: data.leave_days,
    total_hours_worked: data.total_hours,
    average_clock_in: null,
    average_clock_out: null,
  };
}

export interface QRTokenResponse {
  token: string;
  expires_at: string;
  time_remaining: number;
  validity_seconds: number;
}

export const attendanceService = {
  /**
   * Clock in or out
   */
  async clock(data?: {
    qr_token?: string;
    location?: string;
    notes?: string;
  }): Promise<ClockResponse> {
    const response = await api.post<ClockResponse>('/portal/attendance/clock/', data || {});
    return response.data;
  },

  /**
   * Get current QR token (for office display)
   */
  async getQRToken(): Promise<QRTokenResponse> {
    // This endpoint is public, doesn't need auth
    const baseUrl = import.meta.env.VITE_API_URL || '';
    const response = await axios.get<QRTokenResponse>(`${baseUrl}/portal/attendance/qr/token/`);
    return response.data;
  },

  /**
   * Clock in/out using QR code
   */
  async qrClockIn(token: string): Promise<ClockResponse> {
    const response = await api.post<ClockResponse>('/portal/attendance/qr/clock-in/', { token });
    return response.data;
  },

  /**
   * Get today's attendance status
   */
  async getStatus(): Promise<AttendanceStatus> {
    const response = await api.get<ApiClockStatus>('/portal/attendance/status/');
    return toAttendanceStatus(response.data);
  },

  /**
   * Get attendance history
   */
  async getHistory(params?: {
    start_date?: string;
    end_date?: string;
    page_size?: number;
  }): Promise<AttendanceHistory> {
    const response = await api.get<ApiAttendanceRecord[]>('/portal/attendance/history/', {
      params: { from_date: params?.start_date, to_date: params?.end_date },
    });
    return toAttendanceHistory(response.data, params?.page_size);
  },

  /**
   * Get monthly attendance summary
   */
  async getSummary(params?: {
    month?: number;
    year?: number;
  }): Promise<AttendanceSummary> {
    const response = await api.get<ApiAttendanceSummary>('/portal/attendance/summary/', {
      params,
    });
    return toAttendanceSummary(response.data);
  },
};

export default attendanceService;
