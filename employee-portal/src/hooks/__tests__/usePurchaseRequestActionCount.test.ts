import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';

vi.mock('@/services/purchase-request.service', () => ({
  purchaseRequestService: { getMyRequests: vi.fn() },
}));

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { usePurchaseRequestActionCount } = await import('../usePurchaseRequestActionCount');

beforeEach(() => {
  vi.mocked(purchaseRequestService.getMyRequests).mockReset();
});

function item(status: string, id: number) {
  return {
    id,
    requisition_number: `PR-000${id}`,
    requester_id: 1,
    requester_name: 'Riley Requester',
    department_id: 1,
    department_name: 'IT Department',
    status,
    total_estimated_cost: '100.00',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };
}

describe('usePurchaseRequestActionCount', () => {
  it('starts at 0 before the request resolves', () => {
    vi.mocked(purchaseRequestService.getMyRequests).mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => usePurchaseRequestActionCount());
    expect(result.current).toBe(0);
  });

  it('counts only DRAFT and REJECTED requests among the caller\'s own requests', async () => {
    vi.mocked(purchaseRequestService.getMyRequests).mockResolvedValue([
      item('DRAFT', 1),
      item('REJECTED', 2),
      item('PENDING_DEPARTMENT_HEAD', 3),
      item('PROCESSED', 4),
      item('PENDING_ACCOUNTS', 5),
    ] as never);

    const { result } = renderHook(() => usePurchaseRequestActionCount());

    await waitFor(() => expect(result.current).toBe(2));
  });

  it('reports 0 when nothing needs action', async () => {
    vi.mocked(purchaseRequestService.getMyRequests).mockResolvedValue([
      item('PENDING_GM', 1),
      item('PROCESSED', 2),
    ] as never);

    const { result } = renderHook(() => usePurchaseRequestActionCount());

    await waitFor(() => expect(purchaseRequestService.getMyRequests).toHaveBeenCalled());
    expect(result.current).toBe(0);
  });

  it('fails silently and stays at 0 when the request errors', async () => {
    vi.mocked(purchaseRequestService.getMyRequests).mockRejectedValue(new Error('network error'));

    const { result } = renderHook(() => usePurchaseRequestActionCount());

    await waitFor(() => expect(purchaseRequestService.getMyRequests).toHaveBeenCalled());
    expect(result.current).toBe(0);
  });
});
