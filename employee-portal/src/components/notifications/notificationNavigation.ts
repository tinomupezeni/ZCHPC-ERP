import type { Notification } from '@/types/notification.types';

/**
 * Where clicking a notification should take the employee, if anywhere.
 *
 * Slice 3 only wires up Purchase Request notifications: rejected opens the
 * request in edit mode (Review & Correct), processed opens the read-only
 * detail. Every other notification_type/related_object_type returns null -
 * intentionally inert rather than guessing a route for something this slice
 * was never asked to link.
 */
export function purchaseRequestNavigationTarget(notification: Notification): string | null {
  if (
    notification.related_object_type !== 'purchase_request' ||
    notification.related_object_id == null
  ) {
    return null;
  }

  const action = notification.notification_type === 'purchase_request_rejected' ? 'edit' : 'view';
  return `/portal/purchase-requests?requestId=${notification.related_object_id}&action=${action}`;
}
