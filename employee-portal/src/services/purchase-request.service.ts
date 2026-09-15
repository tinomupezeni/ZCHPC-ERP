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

  /**
   * The caller's own purchase requests. Only the "mine" scope is used here -
   * approval queues belong to other portals, not the Employee Portal.
   */
  async getMyRequests(): Promise<PurchaseRequestListItem[]> {
    const response = await api.get<PurchaseRequestListItem[]>('/procurement/requests/', {
      params: { scope: 'mine' },
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
