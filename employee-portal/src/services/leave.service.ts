import api from './api';
import type {
  LeaveType,
  LeaveBalancesResponse,
  LeaveRequest,
  CreateLeaveRequestData,
  LeaveRequestSummary,
  LeaveCalendarEvent,
  LeaveRequestStatus,
} from '@/types/leave.types';

export const leaveService = {
  /**
   * Get all leave types
   */
  async getLeaveTypes(): Promise<LeaveType[]> {
    const response = await api.get<LeaveType[]>('/portal/leave/types/');
    return response.data;
  },

  /**
   * Get employee's leave balances
   */
  async getBalances(year?: number): Promise<LeaveBalancesResponse> {
    const response = await api.get<LeaveBalancesResponse>('/portal/leave/balances/', {
      params: year ? { year } : undefined,
    });
    return response.data;
  },

  /**
   * Get employee's leave requests
   */
  async getRequests(params?: {
    status?: LeaveRequestStatus;
    year?: number;
  }): Promise<LeaveRequest[]> {
    const response = await api.get<LeaveRequest[]>('/portal/leave/requests/', {
      params,
    });
    return response.data;
  },

  /**
   * Get a single leave request
   */
  async getRequest(id: number): Promise<LeaveRequest> {
    const response = await api.get<LeaveRequest>(`/portal/leave/requests/${id}/`);
    return response.data;
  },

  /**
   * Create a new leave request
   */
  async createRequest(data: CreateLeaveRequestData): Promise<LeaveRequest> {
    const response = await api.post<LeaveRequest>('/portal/leave/requests/', data);
    return response.data;
  },

  /**
   * Cancel a pending leave request
   */
  async cancelRequest(id: number): Promise<{ detail: string; request: LeaveRequest }> {
    const response = await api.post<{ detail: string; request: LeaveRequest }>(
      `/portal/leave/requests/${id}/cancel/`
    );
    return response.data;
  },

  /**
   * Get leave request summary statistics
   */
  async getSummary(year?: number): Promise<LeaveRequestSummary> {
    const response = await api.get<LeaveRequestSummary>('/portal/leave/requests/summary/', {
      params: year ? { year } : undefined,
    });
    return response.data;
  },

  /**
   * Get leave requests in calendar format
   */
  async getCalendarEvents(params?: {
    year?: number;
    month?: number;
  }): Promise<LeaveCalendarEvent[]> {
    const response = await api.get<LeaveCalendarEvent[]>('/portal/leave/requests/calendar/', {
      params,
    });
    return response.data;
  },
};

export default leaveService;
