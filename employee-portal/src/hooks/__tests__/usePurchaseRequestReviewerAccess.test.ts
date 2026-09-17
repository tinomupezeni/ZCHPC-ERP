import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';

vi.mock('@/services/purchase-request.service', () => ({
  purchaseRequestService: {
    getPendingDepartmentHeadRequests: vi.fn(),
    getPendingAccountsRequests: vi.fn(),
    getPendingGMRequests: vi.fn(),
    getPendingDirectorRequests: vi.fn(),
  },
}));

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { usePurchaseRequestReviewerAccess } = await import('../usePurchaseRequestReviewerAccess');

beforeEach(() => {
  vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockReset();
  vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockReset();
  vi.mocked(purchaseRequestService.getPendingGMRequests).mockReset();
  vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockReset();
});

function resolveEmpty(...mocks: Array<{ mockResolvedValue: (v: never[]) => void }>) {
  mocks.forEach((m) => m.mockResolvedValue([]));
}

function reject403(...mocks: Array<{ mockRejectedValue: (v: unknown) => void }>) {
  mocks.forEach((m) => m.mockRejectedValue({ response: { status: 403 } }));
}

describe('usePurchaseRequestReviewerAccess', () => {
  it('starts all four flags at null (still checking) before any request resolves', () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockReturnValue(
      new Promise(() => {})
    );
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockReturnValue(
      new Promise(() => {})
    );
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockReturnValue(new Promise(() => {}));
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockReturnValue(
      new Promise(() => {})
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    expect(result.current.canReviewAsDepartmentHead).toBeNull();
    expect(result.current.canVerifyAsAccounts).toBeNull();
    expect(result.current.canRecommendAsGM).toBeNull();
    expect(result.current.canApproveAsDirector).toBeNull();
  });

  it('resolves canReviewAsDepartmentHead to true on a successful (even empty) queue response', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([]);
    reject403(
      vi.mocked(purchaseRequestService.getPendingAccountsRequests),
      vi.mocked(purchaseRequestService.getPendingGMRequests),
      vi.mocked(purchaseRequestService.getPendingDirectorRequests)
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(true));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(false));
    await waitFor(() => expect(result.current.canRecommendAsGM).toBe(false));
    await waitFor(() => expect(result.current.canApproveAsDirector).toBe(false));
  });

  it('resolves canVerifyAsAccounts to true on a successful (even empty) queue response', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([]);
    reject403(
      vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests),
      vi.mocked(purchaseRequestService.getPendingGMRequests),
      vi.mocked(purchaseRequestService.getPendingDirectorRequests)
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(true));
    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(false));
    await waitFor(() => expect(result.current.canRecommendAsGM).toBe(false));
    await waitFor(() => expect(result.current.canApproveAsDirector).toBe(false));
  });

  it('resolves canRecommendAsGM to true on a successful (even empty) queue response (F21)', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([]);
    reject403(
      vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests),
      vi.mocked(purchaseRequestService.getPendingAccountsRequests),
      vi.mocked(purchaseRequestService.getPendingDirectorRequests)
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canRecommendAsGM).toBe(true));
    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(false));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(false));
    await waitFor(() => expect(result.current.canApproveAsDirector).toBe(false));
  });

  it('resolves canApproveAsDirector to true on a successful (even empty) queue response (F22)', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([]);
    reject403(
      vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests),
      vi.mocked(purchaseRequestService.getPendingAccountsRequests),
      vi.mocked(purchaseRequestService.getPendingGMRequests)
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canApproveAsDirector).toBe(true));
    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(false));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(false));
    await waitFor(() => expect(result.current.canRecommendAsGM).toBe(false));
  });

  it('resolves Director access to false when only the other three reviewer permissions are held (F22)', async () => {
    resolveEmpty(
      vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests),
      vi.mocked(purchaseRequestService.getPendingAccountsRequests),
      vi.mocked(purchaseRequestService.getPendingGMRequests)
    );
    reject403(vi.mocked(purchaseRequestService.getPendingDirectorRequests));

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(true));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(true));
    await waitFor(() => expect(result.current.canRecommendAsGM).toBe(true));
    await waitFor(() => expect(result.current.canApproveAsDirector).toBe(false));
  });

  it('resolves all four to false on a 403 from every endpoint', async () => {
    reject403(
      vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests),
      vi.mocked(purchaseRequestService.getPendingAccountsRequests),
      vi.mocked(purchaseRequestService.getPendingGMRequests),
      vi.mocked(purchaseRequestService.getPendingDirectorRequests)
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(false));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(false));
    await waitFor(() => expect(result.current.canRecommendAsGM).toBe(false));
    await waitFor(() => expect(result.current.canApproveAsDirector).toBe(false));
  });

  it('resolves all four to true when the employee holds every reviewer permission', async () => {
    resolveEmpty(
      vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests),
      vi.mocked(purchaseRequestService.getPendingAccountsRequests),
      vi.mocked(purchaseRequestService.getPendingGMRequests),
      vi.mocked(purchaseRequestService.getPendingDirectorRequests)
    );

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(true));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(true));
    await waitFor(() => expect(result.current.canRecommendAsGM).toBe(true));
    await waitFor(() => expect(result.current.canApproveAsDirector).toBe(true));
  });

  it('fails safely to false (not true) on a non-403 error, same as usePurchaseRequestActionCount', async () => {
    const networkError = new Error('Network Error');
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockRejectedValue(
      networkError
    );
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockRejectedValue(networkError);
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockRejectedValue(networkError);
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockRejectedValue(networkError);

    const { result } = renderHook(() => usePurchaseRequestReviewerAccess());

    await waitFor(() => expect(result.current.canReviewAsDepartmentHead).toBe(false));
    await waitFor(() => expect(result.current.canVerifyAsAccounts).toBe(false));
    await waitFor(() => expect(result.current.canRecommendAsGM).toBe(false));
    await waitFor(() => expect(result.current.canApproveAsDirector).toBe(false));
  });
});
