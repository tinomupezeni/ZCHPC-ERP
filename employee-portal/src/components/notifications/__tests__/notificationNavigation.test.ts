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

  it('F19: links a corrected notification to the Department Head review page, not the requester page', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({ notification_type: 'purchase_request_corrected', related_object_id: 24 })
    );
    expect(target).toBe('/portal/purchase-requests/review?requestId=24&action=view');
  });

  it('F27: links a department-head-stage notification to the Department Head review page', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({
        notification_type: 'purchase_request_awaiting_department_head',
        related_object_id: 5,
      })
    );
    expect(target).toBe('/portal/purchase-requests/review?requestId=5&action=view');
  });

  it('F27: links an accounts-stage notification to the Accounts review page', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({
        notification_type: 'purchase_request_awaiting_accounts',
        related_object_id: 6,
      })
    );
    expect(target).toBe('/portal/purchase-requests/accounts?requestId=6&action=view');
  });

  it('F27: links a GM-stage notification to the GM review page', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({
        notification_type: 'purchase_request_awaiting_gm',
        related_object_id: 7,
      })
    );
    expect(target).toBe('/portal/purchase-requests/gm?requestId=7&action=view');
  });

  it('F27: links a director-stage notification to the Director review page', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({
        notification_type: 'purchase_request_awaiting_director',
        related_object_id: 8,
      })
    );
    expect(target).toBe('/portal/purchase-requests/director?requestId=8&action=view');
  });

  it('F27: links a procurement-stage notification to the Procurement review page', () => {
    const target = purchaseRequestNavigationTarget(
      makeNotification({
        notification_type: 'purchase_request_awaiting_procurement',
        related_object_id: 9,
      })
    );
    expect(target).toBe('/portal/purchase-requests/procurement?requestId=9&action=view');
  });

  it('F27: each awaiting-review stage routes to its own page, never a shared or cross-role one', () => {
    const stages: Array<[Notification['notification_type'], string]> = [
      ['purchase_request_awaiting_department_head', 'review'],
      ['purchase_request_awaiting_accounts', 'accounts'],
      ['purchase_request_awaiting_gm', 'gm'],
      ['purchase_request_awaiting_director', 'director'],
      ['purchase_request_awaiting_procurement', 'procurement'],
    ];
    const targets = stages.map(([notification_type]) =>
      purchaseRequestNavigationTarget(makeNotification({ notification_type, related_object_id: 1 }))
    );

    // Every stage must resolve to a distinct destination.
    expect(new Set(targets).size).toBe(stages.length);
    stages.forEach(([, segment], index) => {
      expect(targets[index]).toBe(`/portal/purchase-requests/${segment}?requestId=1&action=view`);
    });
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
