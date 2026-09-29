import api from './api';
import type { Notification } from '@/types/notification.types';

export const notificationService = {
  /** The caller's own notifications, newest first (see NotificationSerializer on the backend). */
  async getNotifications(): Promise<Notification[]> {
    const response = await api.get<Notification[]>('/portal/notifications/');
    return response.data;
  },

  async getUnreadCount(): Promise<number> {
    const response = await api.get<{ unread_count: number }>(
      '/portal/notifications/unread-count/'
    );
    return response.data.unread_count;
  },

  async markAsRead(notificationId: number): Promise<Notification> {
    const response = await api.patch<Notification>(
      `/portal/notifications/${notificationId}/read/`
    );
    return response.data;
  },

  /** Returns how many were marked read, for optimistic unread-count updates. */
  async markAllAsRead(): Promise<number> {
    const response = await api.post<{ marked_read: number }>(
      '/portal/notifications/mark-all-read/'
    );
    return response.data.marked_read;
  },
};

/**
 * Backend errors show up in a few different shapes depending on where they
 * were raised - the same {error}/{detail}/field-error variance
 * getPurchaseRequestErrorMessage in purchase-request.service.ts already
 * handles, kept as a small local copy here rather than a cross-feature
 * import, since notifications aren't otherwise coupled to purchase requests.
 */
export function getNotificationErrorMessage(error: unknown, fallback: string): string {
  const data = (error as { response?: { data?: unknown } })?.response?.data;

  if (!data || typeof data !== 'object') {
    return fallback;
  }

  const record = data as Record<string, unknown>;

  if (typeof record.error === 'string') {
    return record.error;
  }

  if (typeof record.detail === 'string') {
    return record.detail;
  }

  for (const value of Object.values(record)) {
    if (Array.isArray(value) && typeof value[0] === 'string') {
      return value[0];
    }
    if (typeof value === 'string') {
      return value;
    }
  }

  return fallback;
}

export default notificationService;
