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
      getPendingAccountsRequests: vi.fn(),
      getRequest: vi.fn(),
      verifyByAccounts: vi.fn(),
      rejectRequest: vi.fn(),
    },
  };
});

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { PurchaseRequestAccountsReviewPage } = await import(
  '../PurchaseRequestAccountsReviewPage'
);

function queueItem(overrides: Partial<PurchaseRequestListItem> = {}): PurchaseRequestListItem {
  return {
    id: 1,
    requisition_number: 'PR-0042',
    requester_id: 3,
    requester_name: 'Riley Requester',
    department_id: 2,
    department_name: 'IT Department',
    status: 'PENDING_ACCOUNTS',
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
    status: 'PENDING_ACCOUNTS',
    total_estimated_cost: '2400.00',
    items: [
      {
        id: 1,
        description: 'Laptop',
        quantity: 2,
        expected_delivery_period: '2 weeks',
        estimated_cost: '1200.00',
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
    ],
    processed_by: null,
    processed_at: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T09:00:00Z',
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PurchaseRequestAccountsReviewPage />
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
 * disambiguation PurchaseRequestReviewPage.test.tsx uses.
 */
function cardHeadingStillInQueue(): boolean {
  return screen.getAllByText('PR-0042').some((el) => el.tagName === 'H3');
}

describe('PurchaseRequestAccountsReviewPage - queue', () => {
  it('shows a loading state before the queue resolves', () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockReturnValue(
      new Promise(() => {})
    );
    renderPage();

    expect(screen.getByText('Pending Requests')).toBeInTheDocument();
    expect(screen.queryByText('PR-0042')).not.toBeInTheDocument();
  });

  it('renders a successful queue with requisition number, requester, department, total and status', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    renderPage();

    await screen.findByText('PR-0042');
    expect(screen.getByText(/Riley Requester/)).toBeInTheDocument();
    expect(screen.getByText(/IT Department/)).toBeInTheDocument();
    expect(screen.getByText('$2,400.00')).toBeInTheDocument();
    expect(screen.getByText('Awaiting Accounts Verification')).toBeInTheDocument();
  });

  it('shows the empty-queue message for a genuinely empty 200 response', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([]);
    renderPage();

    await screen.findByText('No requests waiting for your review.');
    expect(screen.queryByText("You don't have access to this queue")).not.toBeInTheDocument();
  });

  it('shows a distinct access-denied state for a 403, never the empty-queue message', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockRejectedValue({
      response: { status: 403, data: { error: 'Missing required permission', code: 'PERMISSION_DENIED' } },
    });
    renderPage();

    await screen.findByText('Missing required permission');
    expect(screen.getByText("You don't have access to this queue")).toBeInTheDocument();
    expect(screen.queryByText('No requests waiting for your review.')).not.toBeInTheDocument();
  });

  it('shows a generic error state (with retry) for a non-403 failure', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockRejectedValue(
      new Error('Network Error')
    );
    renderPage();

    await screen.findByText('Failed to load requests awaiting Accounts verification');
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('retries the queue load when Retry is clicked', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests)
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce([queueItem()]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole('button', { name: /retry/i });

    await user.click(screen.getByRole('button', { name: /retry/i }));

    await screen.findByText('PR-0042');
    expect(purchaseRequestService.getPendingAccountsRequests).toHaveBeenCalledTimes(2);
  });

  it('opens the shared detail view when a request row is clicked', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText('PR-0042'));

    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(purchaseRequestService.getRequest).toHaveBeenCalledWith(1);
  });
});

describe('PurchaseRequestAccountsReviewPage - detail', () => {
  it('shows requester, department, requisition number, items, quantities, unit costs, line totals, category, total and decision history', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Riley Requester')).toBeInTheDocument();
    expect(within(dialog).getByText('IT Department')).toBeInTheDocument();
    expect(within(dialog).getByText('PR-0042')).toBeInTheDocument();
    expect(within(dialog).getByText('Laptop')).toBeInTheDocument();
    expect(within(dialog).getByText('Qty: 2')).toBeInTheDocument();
    expect(within(dialog).getByText('Unit Cost: $1,200.00')).toBeInTheDocument();
    expect(within(dialog).getByText('Line Total: $2,400.00')).toBeInTheDocument();
    expect(within(dialog).getByText('Category: IT Equipment')).toBeInTheDocument();
    expect(within(dialog).getByText('$2,400.00')).toBeInTheDocument();
    // Decision history: the earlier Department Head approval is visible.
    expect(within(dialog).getByText('Department Head')).toBeInTheDocument();
    expect(within(dialog).getByText('Approved')).toBeInTheDocument();
  });

  it('renders the detail read-only: no input/textarea controls for editing the request', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).queryAllByRole('textbox')).toHaveLength(0);
    expect(within(dialog).queryAllByRole('spinbutton')).toHaveLength(0);
  });

  it('shows Verify and Reject only when the request is PENDING_ACCOUNTS', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('button', { name: /^verify$/i })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /^reject$/i })).toBeInTheDocument();
  });

  it('hides Verify/Reject when a stale queue row has already moved past PENDING_ACCOUNTS', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      fullRequest({
        status: 'PENDING_GM',
        decisions: [
          { id: 1, stage: 'DEPARTMENT_HEAD', decision: 'APPROVED', actor_id: 11, reason: '', created_at: '2025-01-01T09:00:00Z' },
          { id: 2, stage: 'ACCOUNTS', decision: 'VERIFIED', actor_id: 12, reason: '', created_at: '2025-01-01T10:00:00Z' },
        ],
      })
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).queryByRole('button', { name: /^verify$/i })).not.toBeInTheDocument();
    expect(within(dialog).queryByRole('button', { name: /^reject$/i })).not.toBeInTheDocument();
  });
});

describe('PurchaseRequestAccountsReviewPage - verify', () => {
  async function openVerifyDialog() {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));
    const detailDialog = await screen.findByRole('dialog');
    await user.click(within(detailDialog).getByRole('button', { name: /^verify$/i }));
    return user;
  }

  it('opens a confirmation naming the correct requisition number, with "Verify" (not "Approve") wording', async () => {
    await openVerifyDialog();

    const dialogs = screen.getAllByRole('dialog');
    const verifyDialog = dialogs.find((d) => within(d).queryByText('Verify PR-0042?'));
    expect(verifyDialog).toBeTruthy();
    expect(within(verifyDialog!).queryByText('Approve PR-0042?')).not.toBeInTheDocument();
    expect(
      within(verifyDialog!).queryByRole('button', { name: /^approve$/i })
    ).not.toBeInTheDocument();
  });

  it('describes advancing to the General Manager, not Accounts', async () => {
    await openVerifyDialog();

    expect(
      screen.getByText('This will send the request to the General Manager for review.')
    ).toBeInTheDocument();
    expect(
      screen.queryByText('This will send the request to Accounts for verification.')
    ).not.toBeInTheDocument();
  });

  it('leaves the queue unchanged when cancelled, and does not call verifyByAccounts', async () => {
    const user = await openVerifyDialog();

    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(purchaseRequestService.verifyByAccounts).not.toHaveBeenCalled();
    expect(cardHeadingStillInQueue()).toBe(true);
  });

  it('calls verifyByAccounts with the request id on confirm', async () => {
    vi.mocked(purchaseRequestService.verifyByAccounts).mockResolvedValue(
      fullRequest({ status: 'PENDING_GM' })
    );
    const user = await openVerifyDialog();

    await user.click(screen.getByRole('button', { name: /^verify$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.verifyByAccounts).toHaveBeenCalledWith(1)
    );
  });

  it('on success: removes the request from the queue, shows a toast, and closes the dialogs', async () => {
    vi.mocked(purchaseRequestService.verifyByAccounts).mockResolvedValue(
      fullRequest({ status: 'PENDING_GM' })
    );
    const user = await openVerifyDialog();

    await user.click(screen.getByRole('button', { name: /^verify$/i }));

    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('PR-0042'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('on failure: leaves the request in the queue and shows the mapped server error', async () => {
    vi.mocked(purchaseRequestService.verifyByAccounts).mockRejectedValue({
      response: { data: { error: 'The requester may not act on their own purchase request', code: 'SELF_APPROVAL_FORBIDDEN' } },
    });
    const user = await openVerifyDialog();

    await user.click(screen.getByRole('button', { name: /^verify$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('The requester may not act on their own purchase request')
    );
    expect(cardHeadingStillInQueue()).toBe(true);
  });

  it('disables Verify/Cancel and shows "Verifying..." while the request is in flight', async () => {
    let resolveVerify: (value: PurchaseRequest) => void = () => {};
    vi.mocked(purchaseRequestService.verifyByAccounts).mockReturnValue(
      new Promise((resolve) => {
        resolveVerify = resolve;
      })
    );
    const user = await openVerifyDialog();

    await user.click(screen.getByRole('button', { name: /^verify$/i }));

    expect(screen.getByRole('button', { name: /verifying/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();

    resolveVerify(fullRequest({ status: 'PENDING_GM' }));
    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
  });
});

describe('PurchaseRequestAccountsReviewPage - reject', () => {
  async function openRejectDialog() {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
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

  it('keeps Confirm disabled for a whitespace-only reason', async () => {
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), '   ');

    expect(screen.getByRole('button', { name: /^reject$/i })).toBeDisabled();
  });

  it('enables Confirm once a valid reason is entered', async () => {
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Category needs revisiting');

    expect(screen.getByRole('button', { name: /^reject$/i })).toBeEnabled();
  });

  it('calls rejectRequest with the id and trimmed reason on confirm', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED' })
    );
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Category needs revisiting');
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.rejectRequest).toHaveBeenCalledWith(
        1,
        'Category needs revisiting'
      )
    );
  });

  it('on success: removes the request from the queue, shows a toast, and closes the dialogs', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED' })
    );
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Category needs revisiting');
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

    await user.type(screen.getByLabelText(/reason/i), 'Category needs revisiting');
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('reason: This field may not be blank.')
    );
    expect(cardHeadingStillInQueue()).toBe(true);
    expect(screen.getByLabelText(/reason/i)).toHaveValue('Category needs revisiting');
    expect(screen.getByRole('button', { name: /^reject$/i })).toBeEnabled();
  });
});
