import { describe, expect, it, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { Notification } from '@/types/notification.types';

vi.mock('@/services/notification.service', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/services/notification.service')>();
  return {
    ...actual,
    notificationService: {
      getNotifications: vi.fn(),
      getUnreadCount: vi.fn(),
      markAsRead: vi.fn(),
      markAllAsRead: vi.fn(),
    },
  };
});

const { notificationService } = await import('@/services/notification.service');
const { useNotifications } = await import('../useNotifications');

function makeNotification(overrides: Partial<Notification> = {}): Notification {
  return {
    id: 1,
    notification_type: 'purchase_request_rejected',
    title: 'Purchase Request Rejected',
    message: 'Your purchase requisition PR-00001 was rejected. Reason: Too costly',
    is_read: false,
    created_at: '2025-01-01T00:00:00Z',
    read_at: null,
    related_object_type: 'purchase_request',
    related_object_id: 1,
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(notificationService.getUnreadCount).mockResolvedValue(0);
});

describe('useNotifications - unread count', () => {
  it('loads the unread count on mount', async () => {
    vi.mocked(notificationService.getUnreadCount).mockResolvedValue(3);
    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.unreadCount).toBe(3));
  });

  it('fails silently and stays at 0 when the unread count request errors', async () => {
    vi.mocked(notificationService.getUnreadCount).mockRejectedValue(new Error('network error'));
    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(notificationService.getUnreadCount).toHaveBeenCalled());
    expect(result.current.unreadCount).toBe(0);
  });
});

describe('useNotifications - loading the list', () => {
  it('exposes a loading state while the list request is in flight', async () => {
    vi.mocked(notificationService.getNotifications).mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.loadNotifications();
    });

    await waitFor(() => expect(result.current.isLoading).toBe(true));
  });

  it('populates notifications and derives the unread count from the list', async () => {
    vi.mocked(notificationService.getNotifications).mockResolvedValue([
      makeNotification({ id: 1, is_read: false }),
      makeNotification({ id: 2, is_read: true }),
      makeNotification({ id: 3, is_read: false }),
    ]);
    const { result } = renderHook(() => useNotifications());

    await act(() => result.current.loadNotifications());

    expect(result.current.notifications).toHaveLength(3);
    expect(result.current.unreadCount).toBe(2);
    expect(result.current.error).toBeNull();
  });

  it('shows an empty list without an error when there are no notifications', async () => {
    vi.mocked(notificationService.getNotifications).mockResolvedValue([]);
    const { result } = renderHook(() => useNotifications());

    await act(() => result.current.loadNotifications());

    expect(result.current.notifications).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('exposes an error message and lets the caller retry', async () => {
    vi.mocked(notificationService.getNotifications)
      .mockRejectedValueOnce({ response: { data: { detail: 'Service unavailable' } } })
      .mockResolvedValueOnce([makeNotification()]);
    const { result } = renderHook(() => useNotifications());

    await act(() => result.current.loadNotifications());
    expect(result.current.error).toBe('Service unavailable');
    expect(result.current.notifications).toEqual([]);

    await act(() => result.current.loadNotifications());
    expect(result.current.error).toBeNull();
    expect(result.current.notifications).toHaveLength(1);
  });
});

describe('useNotifications - markAsRead', () => {
  it('optimistically marks the notification read and decrements the unread count', async () => {
    vi.mocked(notificationService.getNotifications).mockResolvedValue([
      makeNotification({ id: 1, is_read: false }),
    ]);
    vi.mocked(notificationService.markAsRead).mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useNotifications());
    await act(() => result.current.loadNotifications());

    act(() => {
      result.current.markAsRead(1);
    });

    expect(result.current.notifications[0].is_read).toBe(true);
    expect(result.current.unreadCount).toBe(0);
    expect(notificationService.markAsRead).toHaveBeenCalledWith(1);
  });

  it('rolls back if the server call fails', async () => {
    vi.mocked(notificationService.getNotifications).mockResolvedValue([
      makeNotification({ id: 1, is_read: false }),
    ]);
    vi.mocked(notificationService.markAsRead).mockRejectedValue(new Error('network error'));
    const { result } = renderHook(() => useNotifications());
    await act(() => result.current.loadNotifications());

    await act(() => result.current.markAsRead(1));

    expect(result.current.notifications[0].is_read).toBe(false);
    expect(result.current.unreadCount).toBe(1);
  });

  it('does nothing for a notification that is already read', async () => {
    vi.mocked(notificationService.getNotifications).mockResolvedValue([
      makeNotification({ id: 1, is_read: true }),
    ]);
    const { result } = renderHook(() => useNotifications());
    await act(() => result.current.loadNotifications());

    await act(() => result.current.markAsRead(1));

    expect(notificationService.markAsRead).not.toHaveBeenCalled();
  });
});

describe('useNotifications - markAllAsRead', () => {
  it('optimistically marks every notification read and zeroes the unread count', async () => {
    vi.mocked(notificationService.getNotifications).mockResolvedValue([
      makeNotification({ id: 1, is_read: false }),
      makeNotification({ id: 2, is_read: false }),
    ]);
    vi.mocked(notificationService.markAllAsRead).mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useNotifications());
    await act(() => result.current.loadNotifications());

    act(() => {
      result.current.markAllAsRead();
    });

    expect(result.current.notifications.every((n) => n.is_read)).toBe(true);
    expect(result.current.unreadCount).toBe(0);
  });

  it('rolls back all of them if the server call fails', async () => {
    vi.mocked(notificationService.getNotifications).mockResolvedValue([
      makeNotification({ id: 1, is_read: false }),
      makeNotification({ id: 2, is_read: false }),
    ]);
    vi.mocked(notificationService.markAllAsRead).mockRejectedValue(new Error('network error'));
    const { result } = renderHook(() => useNotifications());
    await act(() => result.current.loadNotifications());

    await act(() => result.current.markAllAsRead());

    expect(result.current.notifications.every((n) => !n.is_read)).toBe(true);
    expect(result.current.unreadCount).toBe(2);
  });
});
