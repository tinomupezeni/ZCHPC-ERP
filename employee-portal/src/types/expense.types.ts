export interface ExpenseCategory {
  id: number;
  name: string;
  description: string;
  max_amount: number | null;
  requires_receipt: boolean;
}

export type ExpenseStatus = 'Draft' | 'Submitted' | 'Under Review' | 'Approved' | 'Rejected' | 'Paid';

export type ExpenseCurrency = 'USD' | 'ZiG';

export interface ExpenseClaimListItem {
  id: number;
  title: string;
  category: number;
  category_name: string;
  amount: number;
  currency: ExpenseCurrency;
  date_incurred: string;
  status: ExpenseStatus;
  has_receipt: boolean;
  submitted_at: string | null;
  created_at: string;
  can_edit: boolean;
  can_submit: boolean;
  can_cancel: boolean;
}

export interface ExpenseClaimDetail {
  id: number;
  title: string;
  description: string;
  category: number;
  category_name: string;
  amount: number;
  currency: ExpenseCurrency;
  date_incurred: string;
  receipt: string | null;
  receipt_url: string | null;
  status: ExpenseStatus;
  submitted_at: string | null;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_notes: string;
  paid_at: string | null;
  payment_reference: string;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
  can_submit: boolean;
  can_cancel: boolean;
}

export interface CreateExpenseClaimData {
  title: string;
  description?: string;
  category: number;
  amount: number;
  currency: ExpenseCurrency;
  date_incurred: string;
  receipt?: File;
}

export interface UpdateExpenseClaimData {
  title?: string;
  description?: string;
  category?: number;
  amount?: number;
  currency?: ExpenseCurrency;
  date_incurred?: string;
  receipt?: File;
}

export interface ExpenseClaimSummary {
  total_claims: number;
  draft_claims: number;
  pending_claims: number;
  approved_claims: number;
  rejected_claims: number;
  paid_claims: number;
  total_amount_pending: number;
  total_amount_approved: number;
  total_amount_paid: number;
}
