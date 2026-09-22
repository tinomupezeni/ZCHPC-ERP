import { useCallback, useEffect, useState } from 'react';
import {
  notificationService,
  getNotificationErrorMessage,
} from '@/services/notification.service';
import type { Notification } from '@/types/notification.types';

/**
 * Notification bell state: unread count (fetched eagerly, for the badge) and
 * the list itself (fetched lazily, only once the panel is actually opened -
 * see loadNotifications), with optimistic read-state updates that roll back
 * if the server call fails.
 */
export function useNotifications() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadUnreadCount = useCallback(async () => {
    try {
      const count = await notificationService.getUnreadCount();
      setUnreadCount(count);
    } catch {
      // Silent by design, matching usePurchaseRequestActionCount: a badge
      // count isn't worth its own error state - opening the panel surfaces
      // a real one if the employee actually goes looking.
    }
  }, []);

  useEffect(() => {
    loadUnreadCount();
  }, [loadUnreadCount]);

  const loadNotifications = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await notificationService.getNotifications();
      setNotifications(data);
      setUnreadCount(data.filter((n) => !n.is_read).length);
    } catch (err) {
      setError(getNotificationErrorMessage(err, 'Failed to load notifications'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markAsRead = useCallback(
    async (id: number) => {
      const target = notifications.find((n) => n.id === id);
      if (!target || target.is_read) return;

      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));

      try {
        await notificationService.markAsRead(id);
      } catch {
        // Revert - the UI must not claim a read state the server doesn't have.
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: false } : n))
        );
        setUnreadCount((prev) => prev + 1);
      }
    },
    [notifications]
  );

  const markAllAsRead = useCallback(async () => {
    if (unreadCount === 0) return;
    const previousNotifications = notifications;
    const previousUnreadCount = unreadCount;

    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);

    try {
      await notificationService.markAllAsRead();
    } catch {
      setNotifications(previousNotifications);
      setUnreadCount(previousUnreadCount);
    }
  }, [notifications, unreadCount]);

  return {
    unreadCount,
    notifications,
    isLoading,
    error,
    loadNotifications,
    markAsRead,
    markAllAsRead,
  };
}

export default useNotifications;
