import api from './api';
import axios from 'axios';
import type {
  AttendanceStatus,
  AttendanceSummary,
  AttendanceHistory,
  ClockResponse,
} from '@/types/attendance.types';

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
    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
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
    const response = await api.get<AttendanceStatus>('/portal/attendance/status/');
    return response.data;
  },

  /**
   * Get attendance history
   */
  async getHistory(params?: {
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }): Promise<AttendanceHistory> {
    const response = await api.get<AttendanceHistory>('/portal/attendance/history/', {
      params,
    });
    return response.data;
  },

  /**
   * Get monthly attendance summary
   */
  async getSummary(params?: {
    month?: number;
    year?: number;
  }): Promise<AttendanceSummary> {
    const response = await api.get<AttendanceSummary>('/portal/attendance/summary/', {
      params,
    });
    return response.data;
  },
};

export default attendanceService;
