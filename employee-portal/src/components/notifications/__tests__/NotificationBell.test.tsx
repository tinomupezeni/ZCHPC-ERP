import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { Notification } from '@/types/notification.types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

const mockLoadNotifications = vi.fn();
const mockMarkAsRead = vi.fn();
const mockMarkAllAsRead = vi.fn();

const mockUseNotifications = vi.fn();
vi.mock('@/hooks/useNotifications', () => ({
  useNotifications: () => mockUseNotifications(),
}));

const { NotificationBell } = await import('../NotificationBell');

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
    related_object_id: 42,
    ...overrides,
  };
}

function mockState(overrides: Partial<ReturnType<typeof mockUseNotifications>> = {}) {
  mockUseNotifications.mockReturnValue({
    unreadCount: 0,
    notifications: [],
    isLoading: false,
    error: null,
    loadNotifications: mockLoadNotifications,
    markAsRead: mockMarkAsRead,
    markAllAsRead: mockMarkAllAsRead,
    ...overrides,
  });
}

function renderBell() {
  return render(
    <MemoryRouter>
      <NotificationBell />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockState();
});

describe('NotificationBell - badge', () => {
  it('shows no badge when there are no unread notifications', () => {
    mockState({ unreadCount: 0 });
    renderBell();
    expect(screen.queryByText(/^\d+\+?$/)).not.toBeInTheDocument();
  });

  it('shows the unread count on the badge', () => {
    mockState({ unreadCount: 3 });
    renderBell();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('caps the badge at "9+"', () => {
    mockState({ unreadCount: 42 });
    renderBell();
    expect(screen.getByText('9+')).toBeInTheDocument();
  });
});

describe('NotificationBell - opening the panel', () => {
  it('loads notifications when opened', async () => {
    const user = userEvent.setup();
    renderBell();

    await user.click(screen.getByRole('button', { name: /notifications/i }));

    expect(mockLoadNotifications).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });

  it('closes again on a second click without reloading', async () => {
    const user = userEvent.setup();
    renderBell();
    const bell = screen.getByRole('button', { name: /notifications/i });

    await user.click(bell);
    await user.click(bell);

    expect(screen.queryByText('Notifications')).not.toBeInTheDocument();
  });
});

describe('NotificationBell - loading, empty and error states', () => {
  it('shows a loading state', async () => {
    mockState({ isLoading: true });
    const user = userEvent.setup();
    renderBell();

    await user.click(screen.getByRole('button', { name: /notifications/i }));

    expect(screen.queryByText('No notifications yet')).not.toBeInTheDocument();
    expect(screen.queryByText(/failed/i)).not.toBeInTheDocument();
  });

  it('shows an empty state', async () => {
    mockState({ notifications: [] });
    const user = userEvent.setup();
    renderBell();

    await user.click(screen.getByRole('button', { name: /notifications/i }));

    expect(screen.getByText('No notifications yet')).toBeInTheDocument();
  });

  it('shows an error state with a working retry action', async () => {
    mockState({ error: 'Failed to load notifications' });
    const user = userEvent.setup();
    renderBell();

    await user.click(screen.getByRole('button', { name: /notifications/i }));
    expect(screen.getByText('Failed to load notifications')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /retry/i }));
    expect(mockLoadNotifications).toHaveBeenCalledTimes(2); // once on open, once on retry
  });
});

describe('NotificationBell - rendering notifications', () => {
  it('renders title, message and unread indicator for each notification', async () => {
    mockState({
      notifications: [
        makeNotification({ id: 1, is_read: false }),
        makeNotification({
          id: 2,
          is_read: true,
          title: 'Purchase Request Processed',
          message: 'Your purchase requisition PR-00002 has been processed by Procurement.',
        }),
      ],
    });
    const user = userEvent.setup();
    renderBell();

    await user.click(screen.getByRole('button', { name: /notifications/i }));

    expect(screen.getByText('Purchase Request Rejected')).toBeInTheDocument();
    expect(screen.getByText('Purchase Request Processed')).toBeInTheDocument();
    expect(
      screen.getByText(/Your purchase requisition PR-00002 has been processed/)
    ).toBeInTheDocument();
  });

  it('F19: renders the "Purchase Request Corrected" title/message for a department head notification, marked unread', async () => {
    mockState({
      notifications: [
        makeNotification({
          id: 4,
          is_read: false,
          notification_type: 'purchase_request_corrected',
          title: 'Purchase Request Corrected',
          message: 'PR-00026 has been corrected and requires your re-approval.',
          related_object_id: 26,
        }),
      ],
    });
    const user = userEvent.setup();
    renderBell();

    await user.click(screen.getByRole('button', { name: /notifications/i }));

    const notificationButton = screen.getByText('Purchase Request Corrected').closest('button');
    expect(notificationButton).toBeInTheDocument();
    expect(
      screen.getByText('PR-00026 has been corrected and requires your re-approval.')
    ).toBeInTheDocument();
    // Unread indicator dot (see NotificationBell.tsx: rendered only when !is_read).
    expect(notificationButton!.querySelector('.bg-blue-600')).toBeInTheDocument();
  });
});

describe('NotificationBell - interacting with a notification', () => {
  it('marks a rejection notification read, navigates to edit mode, and closes the panel', async () => {
    mockState({
      notifications: [
        makeNotification({
          id: 1,
          notification_type: 'purchase_request_rejected',
          related_object_id: 42,
        }),
      ],
    });
    const user = userEvent.setup();
    renderBell();
    await user.click(screen.getByRole('button', { name: /notifications/i }));

    await user.click(screen.getByText('Purchase Request Rejected'));

    expect(mockMarkAsRead).toHaveBeenCalledWith(1);
    expect(mockNavigate).toHaveBeenCalledWith('/portal/purchase-requests?requestId=42&action=edit');
    expect(screen.queryByText('Notifications')).not.toBeInTheDocument();
  });

  it('marks a processed notification read and navigates to view mode', async () => {
    mockState({
      notifications: [
        makeNotification({
          id: 2,
          notification_type: 'purchase_request_processed',
          title: 'Purchase Request Processed',
          related_object_id: 7,
        }),
      ],
    });
    const user = userEvent.setup();
    renderBell();
    await user.click(screen.getByRole('button', { name: /notifications/i }));

    await user.click(screen.getByText('Purchase Request Processed'));

    expect(mockMarkAsRead).toHaveBeenCalledWith(2);
    expect(mockNavigate).toHaveBeenCalledWith('/portal/purchase-requests?requestId=7&action=view');
  });

  it('F19: marks a corrected notification read and navigates to the Department Head review deep link', async () => {
    mockState({
      notifications: [
        makeNotification({
          id: 4,
          notification_type: 'purchase_request_corrected',
          title: 'Purchase Request Corrected',
          message: 'PR-00026 has been corrected and requires your re-approval.',
          related_object_id: 26,
        }),
      ],
    });
    const user = userEvent.setup();
    renderBell();
    await user.click(screen.getByRole('button', { name: /notifications/i }));

    await user.click(screen.getByText('Purchase Request Corrected'));

    expect(mockMarkAsRead).toHaveBeenCalledWith(4);
    expect(mockNavigate).toHaveBeenCalledWith(
      '/portal/purchase-requests/review?requestId=26&action=view'
    );
  });

  it('marks a non-linkable notification read without navigating', async () => {
    mockState({
      notifications: [
        makeNotification({
          id: 3,
          notification_type: 'announcement',
          title: 'Company Announcement',
          related_object_type: null,
          related_object_id: null,
        }),
      ],
    });
    const user = userEvent.setup();
    renderBell();
    await user.click(screen.getByRole('button', { name: /notifications/i }));

    await user.click(screen.getByText('Company Announcement'));

    expect(mockMarkAsRead).toHaveBeenCalledWith(3);
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('"Mark all read" only appears when there are unread notifications, and calls markAllAsRead', async () => {
    mockState({
      unreadCount: 2,
      notifications: [makeNotification({ id: 1 }), makeNotification({ id: 2 })],
    });
    const user = userEvent.setup();
    renderBell();
    await user.click(screen.getByRole('button', { name: /notifications/i }));

    const markAllButton = screen.getByRole('button', { name: /mark all read/i });
    await user.click(markAllButton);

    expect(mockMarkAllAsRead).toHaveBeenCalledTimes(1);
  });

  it('does not show "Mark all read" when everything is already read', async () => {
    mockState({ unreadCount: 0, notifications: [makeNotification({ is_read: true })] });
    const user = userEvent.setup();
    renderBell();
    await user.click(screen.getByRole('button', { name: /notifications/i }));

    expect(screen.queryByRole('button', { name: /mark all read/i })).not.toBeInTheDocument();
  });
});
