import api from './api';
import type {
  PurchaseRequest,
  PurchaseRequestCategory,
  PurchaseRequestListItem,
  CreatePurchaseRequestData,
  UpdatePurchaseRequestData,
} from '@/types/purchase-request.types';

export const purchaseRequestService = {
  /**
   * Employee-facing Purchase Request categories (F11-A). id + name only -
   * the underlying AccountChart/GL code never reaches the client.
   */
  async getCategories(): Promise<PurchaseRequestCategory[]> {
    const response = await api.get<PurchaseRequestCategory[]>(
      '/procurement/purchase-request-categories/'
    );
    return response.data;
  },

  /** The caller's own purchase requests. */
  async getMyRequests(): Promise<PurchaseRequestListItem[]> {
    const response = await api.get<PurchaseRequestListItem[]>('/procurement/requests/', {
      params: { scope: 'mine' },
    });
    return response.data;
  },

  /**
   * F17: requests awaiting the caller's department-head review. The backend
   * pre-filters this to departments the caller is actually recorded as
   * heading - a 403 here means the caller holds no department-head
   * authority at all, which callers must surface distinctly from a
   * genuinely empty queue rather than treating both the same way.
   */
  async getPendingDepartmentHeadRequests(): Promise<PurchaseRequestListItem[]> {
    const response = await api.get<PurchaseRequestListItem[]>('/procurement/requests/', {
      params: { scope: 'pending-department-head' },
    });
    return response.data;
  },

  /**
   * F18: requests awaiting Accounts verification. Unlike the department-head
   * queue, this scope is organization-wide, not pre-filtered by the backend
   * to anything about the caller - any authenticated actor holding
   * accounts_verify sees every request currently at this stage. A 403 here
   * means the caller holds no Accounts capability at all, which callers
   * must surface distinctly from a genuinely empty queue.
   */
  async getPendingAccountsRequests(): Promise<PurchaseRequestListItem[]> {
    const response = await api.get<PurchaseRequestListItem[]>('/procurement/requests/', {
      params: { scope: 'pending-accounts' },
    });
    return response.data;
  },

  /**
   * F21: requests awaiting GM recommendation. Same shape as Accounts -
   * organization-wide (authorize_gm_recommendation has no department-scoping
   * check, unlike department-head approval), gated purely on the
   * gm_recommend permission. A 403 means the caller holds no GM capability
   * at all, distinct from a genuinely empty queue.
   */
  async getPendingGMRequests(): Promise<PurchaseRequestListItem[]> {
    const response = await api.get<PurchaseRequestListItem[]>('/procurement/requests/', {
      params: { scope: 'pending-gm' },
    });
    return response.data;
  },

  async getRequest(id: number): Promise<PurchaseRequest> {
    const response = await api.get<PurchaseRequest>(`/procurement/requests/${id}/`);
    return response.data;
  },

  /** Step 1 of the two-step create flow: raises a DRAFT request. */
  async createRequest(data: CreatePurchaseRequestData): Promise<PurchaseRequest> {
    const response = await api.post<PurchaseRequest>('/procurement/requests/', data);
    return response.data;
  },

  /** Step 2: moves a DRAFT request into the approval workflow. */
  async submitRequest(id: number): Promise<PurchaseRequest> {
    const response = await api.post<PurchaseRequest>(`/procurement/requests/${id}/submit/`);
    return response.data;
  },

  /**
   * Slice 2: replace a DRAFT/REJECTED request's entire item collection. A
   * REJECTED request is returned to DRAFT by the backend as part of this
   * same call (see UpdatePurchaseRequestItems) - no separate
   * correct-and-resubmit call is needed from here.
   */
  async updateItems(id: number, data: UpdatePurchaseRequestData): Promise<PurchaseRequest> {
    const response = await api.patch<PurchaseRequest>(`/procurement/requests/${id}/`, data);
    return response.data;
  },

  /**
   * Slice 4: permanently delete a DRAFT request the caller owns. The
   * backend is authoritative on what's deletable (DRAFT, no decision
   * history) - this call can fail with a 400/403/404, which the caller
   * must surface rather than assume success.
   */
  async deleteRequest(id: number): Promise<void> {
    await api.delete(`/procurement/requests/${id}/`);
  },

  /** F17: approve a request currently awaiting the caller's department-head review. */
  async approveByDepartmentHead(id: number): Promise<PurchaseRequest> {
    const response = await api.post<PurchaseRequest>(
      `/procurement/requests/${id}/department-head/approve/`
    );
    return response.data;
  },

  /** F18: verify a request currently awaiting Accounts verification. */
  async verifyByAccounts(id: number): Promise<PurchaseRequest> {
    const response = await api.post<PurchaseRequest>(
      `/procurement/requests/${id}/accounts/verify/`
    );
    return response.data;
  },

  /**
   * F21: recommend a request currently awaiting GM review. Moves it to
   * PENDING_DIRECTOR on success (RecommendPurchaseRequestByGM) - no request
   * body, same full-detail response shape as approve/verify.
   */
  async recommendByGM(id: number): Promise<PurchaseRequest> {
    const response = await api.post<PurchaseRequest>(`/procurement/requests/${id}/gm/recommend/`);
    return response.data;
  },

  /**
   * F17: reject a request. The backend endpoint is stage-aware - it rejects
   * at whatever stage the request currently sits at, rather than needing a
   * separate route per approving office - so this one method is already
   * correct for Accounts/GM/Director's own reject action, not just the
   * department-head stage.
   */
  async rejectRequest(id: number, reason: string): Promise<PurchaseRequest> {
    const response = await api.post<PurchaseRequest>(`/procurement/requests/${id}/reject/`, {
      reason,
    });
    return response.data;
  },
};

/**
 * Backend errors show up in a few different shapes depending on where they
 * were raised (see purchase_request_views._handle_domain_error for the
 * {error, code} shape, DRF's own {detail} for auth/routing failures, and
 * plain serializer field-error dicts for shape validation). This picks a
 * human-readable message out of whichever shape actually comes back.
 */
export function getPurchaseRequestErrorMessage(error: unknown, fallback: string): string {
  const data = (error as { response?: { data?: unknown } })?.response?.data;

  if (!data || typeof data !== 'object') {
    return fallback;
  }

  const record = data as Record<string, unknown>;

  if (typeof record.error === 'string') {
    return record.error;
  }

  if (typeof record.detail === 'string') {
    return record.detail;
  }

  // DRF field-validation errors: { field: ["message", ...], ... }
  for (const value of Object.values(record)) {
    if (Array.isArray(value) && typeof value[0] === 'string') {
      return value[0];
    }
    if (typeof value === 'string') {
      return value;
    }
  }

  return fallback;
}

export default purchaseRequestService;
