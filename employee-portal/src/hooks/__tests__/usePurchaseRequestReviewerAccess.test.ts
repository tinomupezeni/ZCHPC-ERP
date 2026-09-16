import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';

vi.mock('@/services/purchase-request.service', () => ({
  purchaseRequestService: {
    getPendingDepartmentHeadRequests: vi.fn(),
    getPendingAccountsRequests: vi.fn(),
  },
}));

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { usePurchaseRequestReviewerAccess } = await import('../usePurchaseRequestReviewerAccess');

beforeEach(() => {
  vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockReset();
  vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockReset();
});

describe('usePurchaseRequestReviewerAccess', () => {
  it('starts both flags at null (still checking) before either request resolves', () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockReturnValue(
      new Promise(() => {})
    );
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockReturnValue(
      new Promise(() => {})
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    expect(result.current.canReviewAsDepartmentHead).toBeNull();
    expect(result.current.canVerifyAsAccounts).toBeNull();
  });

  it('resolves canReviewAsDepartmentHead to true on a successful (even empty) queue response', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([]);
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockRejectedValue({
      response: { status: 403 },
    });

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(true));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(false));
  });

  it('resolves canVerifyAsAccounts to true on a successful (even empty) queue response', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([]);
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockRejectedValue({
      response: { status: 403 },
    });

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(true));
    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(false));
  });

  it('resolves both to false on a 403 from both endpoints', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockRejectedValue({
      response: { status: 403 },
    });
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockRejectedValue({
      response: { status: 403 },
    });

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(false));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(false));
  });

  it('resolves both to true when the employee holds both reviewer permissions', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([]);
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([]);

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(true));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(true));
  });

  it('fails safely to false (not true) on a non-403 error, same as usePurchaseRequestActionCount', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockRejectedValue(
      new Error('Network Error')
    );
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockRejectedValue(
      new Error('Network Error')
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(false));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(false));
  });
});
