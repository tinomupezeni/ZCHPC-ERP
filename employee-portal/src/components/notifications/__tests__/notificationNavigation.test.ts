import { describe, expect, it } from 'vitest';
import { purchaseRequestNavigationTarget } from '../notificationNavigation';
import type { Notification } from '@/types/notification.types';

function makeNotification(overrides: Partial<Notification> = {}): Notification {
  return {
    id: 1,
    notification_type: 'purchase_request_rejected',
    title: 'Purchase Request Rejected',
    message: 'msg',
    is_read: false,
    created_at: '2025-01-01T00:00:00Z',
    read_at: null,
    related_object_type: 'purchase_request',
    related_object_id: 42,
    ...overrides,
  };
}

describe('purchaseRequestNavigationTarget', () => {
  it('links a rejected notification to edit mode (Review & Correct)', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({ notification_type: 'purchase_request_rejected', related_object_id: 42 })
    );
    expect(target).toBe('/portal/purchase-requests?requestId=42&action=edit');
  });

  it('links a processed notification to view mode', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({ notification_type: 'purchase_request_processed', related_object_id: 7 })
    );
    expect(target).toBe('/portal/purchase-requests?requestId=7&action=view');
  });

  it('returns null when related_object_type is not a purchase request', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({ related_object_type: 'leave_request', related_object_id: 1 })
    );
    expect(target).toBeNull();
  });

  it('returns null when there is no related object at all', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({ related_object_type: null, related_object_id: null })
    );
    expect(target).toBeNull();
  });
});
