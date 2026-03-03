import api from './api';
import type { DashboardSummary, Notification } from '@/types/dashboard.types';

export const dashboardService = {
  /**
   * Get dashboard summary data
   */
  async getDashboard(): Promise<DashboardSummary> {
    const response = await api.get<DashboardSummary>('/portal/dashboard/');
    return response.data;
  },

  /**
   * Get notifications list
   */
  async getNotifications(params?: {
    is_read?: boolean;
    type?: string;
  }): Promise<Notification[]> {
    const response = await api.get<Notification[]>('/portal/notifications/', {
      params,
    });
    return response.data;
  },

  /**
   * Mark a notification as read
   */
  async markAsRead(notificationId: number): Promise<Notification> {
    const response = await api.patch<Notification>(
      `/portal/notifications/${notificationId}/read/`
    );
    return response.data;
  },

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<{ detail: string }> {
    const response = await api.post<{ detail: string }>(
      '/portal/notifications/mark-all-read/'
    );
    return response.data;
  },

  /**
   * Get unread notification count
   */
  async getUnreadCount(): Promise<number> {
    const response = await api.get<{ count: number }>(
      '/portal/notifications/unread_count/'
    );
    return response.data.count;
  },
};

export default dashboardService;
