import api from './api';
import type {
  ExpenseCategory,
  ExpenseClaimListItem,
  ExpenseClaimDetail,
  CreateExpenseClaimData,
  UpdateExpenseClaimData,
  ExpenseClaimSummary,
  ExpenseStatus,
} from '@/types/expense.types';

export const expenseService = {
  /**
   * Get expense categories
   */
  async getCategories(): Promise<ExpenseCategory[]> {
    const response = await api.get<ExpenseCategory[]>('/portal/expenses/categories/');
    return response.data;
  },

  /**
   * Get list of expense claims
   */
  async getClaims(params?: {
    status?: ExpenseStatus;
    start_date?: string;
    end_date?: string;
  }): Promise<ExpenseClaimListItem[]> {
    const response = await api.get<ExpenseClaimListItem[]>('/portal/expenses/', {
      params,
    });
    return response.data;
  },

  /**
   * Get expense claim details
   */
  async getClaim(id: number): Promise<ExpenseClaimDetail> {
    const response = await api.get<ExpenseClaimDetail>(`/portal/expenses/${id}/`);
    return response.data;
  },

  /**
   * Create a new expense claim
   */
  async createClaim(data: CreateExpenseClaimData): Promise<ExpenseClaimDetail> {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('category', data.category.toString());
    formData.append('amount', data.amount.toString());
    formData.append('currency', data.currency);
    formData.append('date_incurred', data.date_incurred);

    if (data.description) {
      formData.append('description', data.description);
    }
    if (data.receipt) {
      formData.append('receipt', data.receipt);
    }

    const response = await api.post<ExpenseClaimDetail>('/portal/expenses/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Update a draft expense claim
   */
  async updateClaim(id: number, data: UpdateExpenseClaimData): Promise<ExpenseClaimDetail> {
    const formData = new FormData();

    if (data.title) formData.append('title', data.title);
    if (data.category) formData.append('category', data.category.toString());
    if (data.amount) formData.append('amount', data.amount.toString());
    if (data.currency) formData.append('currency', data.currency);
    if (data.date_incurred) formData.append('date_incurred', data.date_incurred);
    if (data.description !== undefined) formData.append('description', data.description);
    if (data.receipt) formData.append('receipt', data.receipt);

    const response = await api.patch<ExpenseClaimDetail>(`/portal/expenses/${id}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Delete a draft expense claim
   */
  async deleteClaim(id: number): Promise<void> {
    await api.delete(`/portal/expenses/${id}/`);
  },

  /**
   * Submit a draft claim for review
   */
  async submitClaim(id: number): Promise<{ detail: string; claim: ExpenseClaimDetail }> {
    const response = await api.post<{ detail: string; claim: ExpenseClaimDetail }>(
      `/portal/expenses/${id}/submit/`
    );
    return response.data;
  },

  /**
   * Cancel a draft or submitted claim
   */
  async cancelClaim(id: number): Promise<{ detail: string }> {
    const response = await api.post<{ detail: string }>(`/portal/expenses/${id}/cancel/`);
    return response.data;
  },

  /**
   * Get expense claims summary
   */
  async getSummary(): Promise<ExpenseClaimSummary> {
    const response = await api.get<ExpenseClaimSummary>('/portal/expenses/summary/');
    return response.data;
  },
};

export default expenseService;
