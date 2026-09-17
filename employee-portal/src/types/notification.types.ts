export type NotificationType =
  | 'leave_approved'
  | 'leave_rejected'
  | 'leave_request'
  | 'expense_approved'
  | 'expense_rejected'
  | 'ticket_update'
  | 'ticket_resolved'
  | 'payslip_available'
  | 'announcement'
  | 'system'
  | 'purchase_request_rejected'
  | 'purchase_request_processed'
  | 'purchase_request_corrected';

export interface Notification {
  id: number;
  notification_type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
  /**
   * What this notification is about, e.g. "purchase_request" - lets the
   * frontend deep-link into the relevant record. Both null together for
   * notification types (e.g. announcements) that aren't about a specific
   * record.
   */
  related_object_type: string | null;
  related_object_id: number | null;
}
