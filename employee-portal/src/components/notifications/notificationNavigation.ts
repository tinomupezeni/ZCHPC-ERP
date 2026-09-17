import type { Notification } from '@/types/notification.types';

/**
 * Where clicking a notification should take the employee, if anywhere.
 *
 * Slice 3 wires up the requester-facing Purchase Request notifications:
 * rejected opens the request in edit mode (Review & Correct), processed
 * opens the read-only detail - both on the requester's own
 * /portal/purchase-requests page. F19 adds the one department-head-facing
 * notification (a corrected request awaiting re-approval), which instead
 * opens the existing Department Head review page - a different recipient
 * needs a different destination, not just different copy. Every other
 * notification_type/related_object_type returns null - intentionally inert
 * rather than guessing a route for something this slice was never asked to
 * link.
 */
export function purchaseRequestNavigationTarget(notification: Notification): string | null {
  if (
    notification.related_object_type !== 'purchase_request' ||
    notification.related_object_id == null
  ) {
    return null;
  }

  if (notification.notification_type === 'purchase_request_corrected') {
    return `/portal/purchase-requests/review?requestId=${notification.related_object_id}&action=view`;
  }

  const action = notification.notification_type === 'purchase_request_rejected' ? 'edit' : 'view';
  return `/portal/purchase-requests?requestId=${notification.related_object_id}&action=${action}`;
}
