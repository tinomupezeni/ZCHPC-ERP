import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { toast } from 'sonner';
import type { PurchaseRequest, PurchaseRequestListItem } from '@/types/purchase-request.types';

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock('@/services/purchase-request.service', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/services/purchase-request.service')>();
  return {
    ...actual,
    purchaseRequestService: {
      getPendingGMRequests: vi.fn(),
      getRequest: vi.fn(),
      recommendByGM: vi.fn(),
      rejectRequest: vi.fn(),
    },
  };
});

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { PurchaseRequestGMReviewPage } = await import('../PurchaseRequestGMReviewPage');

function queueItem(overrides: Partial<PurchaseRequestListItem> = {}): PurchaseRequestListItem {
  return {
    id: 1,
    requisition_number: 'PR-0042',
    requester_id: 3,
    requester_name: 'Riley Requester',
    department_id: 2,
    department_name: 'IT Department',
    status: 'PENDING_GM',
    total_estimated_cost: '2400.00',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

function fullRequest(overrides: Partial<PurchaseRequest> = {}): PurchaseRequest {
  return {
    id: 1,
    requisition_number: 'PR-0042',
    requester_id: 3,
    requester_name: 'Riley Requester',
    department_id: 2,
    department_name: 'IT Department',
    designation: 'Technician',
    contact: '+263771111111',
    status: 'PENDING_GM',
    total_estimated_cost: '2400.00',
    items: [
      {
        id: 1,
        description: 'Laptop',
        quantity: 2,
        expected_delivery_period: '2 weeks',
        estimated_cost: '1200.00',
        category_id: 1,
        budget_code_id: 42,
        category: { id: 5, name: 'IT Equipment', is_active: true },
      },
    ],
    decisions: [
      {
        id: 1,
        stage: 'DEPARTMENT_HEAD',
        decision: 'APPROVED',
        actor_id: 11,
        reason: '',
        created_at: '2025-01-01T09:00:00Z',
      },
      {
        id: 2,
        stage: 'ACCOUNTS',
        decision: 'VERIFIED',
        actor_id: 12,
        reason: '',
        created_at: '2025-01-01T10:00:00Z',
      },
    ],
    processed_by: null,
    processed_at: null,
    purchase_order_number: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T10:00:00Z',
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PurchaseRequestGMReviewPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

/**
 * With the detail dialog open, Radix marks the rest of the page aria-hidden
 * for screen readers, so getByRole can no longer see the queue card's
 * heading behind the modal even though it's still in the DOM - same
 * disambiguation PurchaseRequestReviewPage.test.tsx/
 * PurchaseRequestAccountsReviewPage.test.tsx use.
 */
function cardHeadingStillInQueue(): boolean {
  return screen.getAllByText('PR-0042').some((el) => el.tagName === 'H3');
}

describe('PurchaseRequestGMReviewPage - queue', () => {
  it('shows a loading state before the queue resolves', () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockReturnValue(
      new Promise(() => {})
    );
    renderPage();

    expect(screen.getByText('Pending Requests')).toBeInTheDocument();
    expect(screen.queryByText('PR-0042')).not.toBeInTheDocument();
  });

  it('renders a successful queue with requisition number, requester, department, total and status', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    renderPage();

    await screen.findByText('PR-0042');
    expect(screen.getByText(/Riley Requester/)).toBeInTheDocument();
    expect(screen.getByText(/IT Department/)).toBeInTheDocument();
    expect(screen.getByText('$2,400.00')).toBeInTheDocument();
    expect(screen.getByText('Awaiting General Manager')).toBeInTheDocument();
  });

  it('shows the empty-queue message for a genuinely empty 200 response', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([]);
    renderPage();

    await screen.findByText('No requests waiting for your review.');
    expect(screen.queryByText("You don't have access to this queue")).not.toBeInTheDocument();
  });

  it('shows a distinct access-denied state for a 403, never the empty-queue message', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockRejectedValue({
      response: { status: 403, data: { error: 'Missing required permission', code: 'PERMISSION_DENIED' } },
    });
    renderPage();

    expect(await screen.findByText("You don't have access to this queue")).toBeInTheDocument();
    expect(
      screen.getByText('You do not have access to the GM recommendation queue.')
    ).toBeInTheDocument();
    expect(screen.queryByText('No requests waiting for your review.')).not.toBeInTheDocument();
  });

  it('never shows the backend\'s raw permission identifier for a 403', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockRejectedValue({
      response: {
        status: 403,
        data: {
          error: "Missing required permission 'procurement.purchase_request.gm_recommend'",
          code: 'PERMISSION_DENIED',
        },
      },
    });
    renderPage();

    await screen.findByText("You don't have access to this queue");
    expect(screen.queryByText(/missing required permission/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/procurement\.purchase_request/i)).not.toBeInTheDocument();
  });

  it('shows a generic error state (with retry) for a non-403 failure', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockRejectedValue(
      new Error('Network Error')
    );
    renderPage();

    await screen.findByText('Failed to load requests awaiting GM recommendation');
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('retries the queue load when Retry is clicked', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests)
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce([queueItem()]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole('button', { name: /retry/i });

    await user.click(screen.getByRole('button', { name: /retry/i }));

    await screen.findByText('PR-0042');
    expect(purchaseRequestService.getPendingGMRequests).toHaveBeenCalledTimes(2);
  });

  it('opens the shared detail view when a request row is clicked', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText('PR-0042'));

    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(purchaseRequestService.getRequest).toHaveBeenCalledWith(1);
  });
});

describe('PurchaseRequestGMReviewPage - detail', () => {
  it('shows requester, department, requisition number, items, quantities, unit costs, line totals, category, total and decision history', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Riley Requester')).toBeInTheDocument();
    expect(within(dialog).getAllByText('IT Department').length).toBeGreaterThan(0);
    expect(within(dialog).getAllByText('PR-0042').length).toBeGreaterThan(0);
    const itemRow = within(dialog).getByText('Laptop').closest('tr')!;
    expect(within(itemRow).getByText('Delivery: 2 weeks')).toBeInTheDocument();
    expect(within(itemRow).getByText('IT Equipment')).toBeInTheDocument();
    const cells = within(itemRow).getAllByRole('cell');
    expect(cells[3]).toHaveTextContent('2'); // Qty
    expect(cells[4]).toHaveTextContent('$1,200.00'); // Unit Cost
    expect(cells[5]).toHaveTextContent('$2,400.00'); // Line Total
    expect(
      within(dialog).getByText('Total Estimated Cost').closest('div')
    ).toHaveTextContent('$2,400.00');
    // Decision history: the earlier Department Head + Accounts stages are visible.
    expect(within(dialog).getByText('Department Head')).toBeInTheDocument();
    expect(within(dialog).getAllByText('Approved').length).toBeGreaterThan(0);
    expect(within(dialog).getByText('Verified')).toBeInTheDocument();
  });

  it('F21: shows GM reviewer-oriented status copy ("Awaiting Your Recommendation"), not requester-oriented copy', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Awaiting Your Recommendation')).toBeInTheDocument();
    expect(
      within(dialog).getByText('This request requires your recommendation.')
    ).toBeInTheDocument();
    expect(within(dialog).queryByText(/no action needed/i)).not.toBeInTheDocument();
    expect(
      within(dialog).queryByText('Verified by Accounts — the General Manager is reviewing it next.')
    ).not.toBeInTheDocument();
  });

  it('renders the detail read-only: no input/textarea controls for editing the request', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).queryAllByRole('textbox')).toHaveLength(0);
    expect(within(dialog).queryAllByRole('spinbutton')).toHaveLength(0);
  });

  it('shows Recommend and Reject only when the request is PENDING_GM', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('button', { name: /^recommend$/i })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /^reject$/i })).toBeInTheDocument();
  });

  it('hides Recommend/Reject when a stale queue row has already moved past PENDING_GM', async () => {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      fullRequest({
        status: 'PENDING_DIRECTOR',
        decisions: [
          { id: 1, stage: 'DEPARTMENT_HEAD', decision: 'APPROVED', actor_id: 11, reason: '', created_at: '2025-01-01T09:00:00Z' },
          { id: 2, stage: 'ACCOUNTS', decision: 'VERIFIED', actor_id: 12, reason: '', created_at: '2025-01-01T10:00:00Z' },
          { id: 3, stage: 'GM', decision: 'RECOMMENDED', actor_id: 13, reason: '', created_at: '2025-01-01T11:00:00Z' },
        ],
      })
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).queryByRole('button', { name: /^recommend$/i })).not.toBeInTheDocument();
    expect(within(dialog).queryByRole('button', { name: /^reject$/i })).not.toBeInTheDocument();
  });
});

describe('PurchaseRequestGMReviewPage - recommend', () => {
  async function openRecommendDialog() {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));
    const detailDialog = await screen.findByRole('dialog');
    await user.click(within(detailDialog).getByRole('button', { name: /^recommend$/i }));
    return user;
  }

  it('opens a confirmation naming the correct requisition number, with "Recommend" (not "Approve") wording', async () => {
    await openRecommendDialog();

    const dialogs = screen.getAllByRole('dialog');
    const recommendDialog = dialogs.find((d) => within(d).queryByText('Recommend PR-0042?'));
    expect(recommendDialog).toBeTruthy();
    expect(within(recommendDialog!).queryByText('Approve PR-0042?')).not.toBeInTheDocument();
    expect(
      within(recommendDialog!).queryByRole('button', { name: /^approve$/i })
    ).not.toBeInTheDocument();
  });

  it('describes advancing to the Director, not Accounts or the General Manager', async () => {
    await openRecommendDialog();

    expect(
      screen.getByText('This will send the request to the Director for review.')
    ).toBeInTheDocument();
    expect(
      screen.queryByText('This will send the request to Accounts for verification.')
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText('This will send the request to the General Manager for review.')
    ).not.toBeInTheDocument();
  });

  it('leaves the queue unchanged when cancelled, and does not call recommendByGM', async () => {
    const user = await openRecommendDialog();

    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(purchaseRequestService.recommendByGM).not.toHaveBeenCalled();
    expect(cardHeadingStillInQueue()).toBe(true);
  });

  it('calls recommendByGM with the request id on confirm', async () => {
    vi.mocked(purchaseRequestService.recommendByGM).mockResolvedValue(
      fullRequest({ status: 'PENDING_DIRECTOR' })
    );
    const user = await openRecommendDialog();

    await user.click(screen.getByRole('button', { name: /^recommend$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.recommendByGM).toHaveBeenCalledWith(1)
    );
  });

  it('on success: removes the request from the queue, shows a toast, and closes the dialogs', async () => {
    vi.mocked(purchaseRequestService.recommendByGM).mockResolvedValue(
      fullRequest({ status: 'PENDING_DIRECTOR' })
    );
    const user = await openRecommendDialog();

    await user.click(screen.getByRole('button', { name: /^recommend$/i }));

    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('PR-0042'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('on failure: leaves the request in the queue and shows the mapped server error', async () => {
    vi.mocked(purchaseRequestService.recommendByGM).mockRejectedValue({
      response: { data: { error: 'The requester may not act on their own purchase request', code: 'SELF_APPROVAL_FORBIDDEN' } },
    });
    const user = await openRecommendDialog();

    await user.click(screen.getByRole('button', { name: /^recommend$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('The requester may not act on their own purchase request')
    );
    expect(cardHeadingStillInQueue()).toBe(true);
  });

  it('disables Recommend/Cancel and shows "Recommending..." while the request is in flight', async () => {
    let resolveRecommend: (value: PurchaseRequest) => void = () => {};
    vi.mocked(purchaseRequestService.recommendByGM).mockReturnValue(
      new Promise((resolve) => {
        resolveRecommend = resolve;
      })
    );
    const user = await openRecommendDialog();

    await user.click(screen.getByRole('button', { name: /^recommend$/i }));

    expect(screen.getByRole('button', { name: /recommending/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();

    resolveRecommend(fullRequest({ status: 'PENDING_DIRECTOR' }));
    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
  });
});

describe('PurchaseRequestGMReviewPage - reject', () => {
  async function openRejectDialog() {
    vi.mocked(purchaseRequestService.getPendingGMRequests).mockResolvedValue([queueItem()]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));
    const detailDialog = await screen.findByRole('dialog');
    await user.click(within(detailDialog).getByRole('button', { name: /^reject$/i }));
    return user;
  }

  it('opens a dialog naming the correct requisition number', async () => {
    await openRejectDialog();

    expect(screen.getByText('Reject PR-0042')).toBeInTheDocument();
  });

  it('keeps Confirm disabled for a blank reason', async () => {
    await openRejectDialog();

    expect(screen.getByRole('button', { name: /^reject$/i })).toBeDisabled();
  });

  it('enables Confirm once a valid reason is entered', async () => {
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Budget exceeds departmental allocation');

    expect(screen.getByRole('button', { name: /^reject$/i })).toBeEnabled();
  });

  it('calls rejectRequest with the id and trimmed reason on confirm, preserving the reason', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED' })
    );
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Budget exceeds departmental allocation');
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.rejectRequest).toHaveBeenCalledWith(
        1,
        'Budget exceeds departmental allocation'
      )
    );
  });

  it('on success: removes the request from the queue, shows a toast, and closes the dialogs', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED' })
    );
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Budget exceeds departmental allocation');
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('PR-0042'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('on failure: leaves the request in the queue, shows the mapped server error, and the reason is retryable', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockRejectedValue({
      response: { data: { error: 'reason: This field may not be blank.' } },
    });
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Budget exceeds departmental allocation');
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('reason: This field may not be blank.')
    );
    expect(cardHeadingStillInQueue()).toBe(true);
    expect(screen.getByLabelText(/reason/i)).toHaveValue('Budget exceeds departmental allocation');
    expect(screen.getByRole('button', { name: /^reject$/i })).toBeEnabled();
  });
});
