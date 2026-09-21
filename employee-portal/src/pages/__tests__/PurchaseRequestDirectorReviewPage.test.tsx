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
      getPendingDirectorRequests: vi.fn(),
      getRequest: vi.fn(),
      approveByDirector: vi.fn(),
      rejectRequest: vi.fn(),
    },
  };
});

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { PurchaseRequestDirectorReviewPage } = await import(
  '../PurchaseRequestDirectorReviewPage'
);

function queueItem(overrides: Partial<PurchaseRequestListItem> = {}): PurchaseRequestListItem {
  return {
    id: 1,
    requisition_number: 'PR-0042',
    requester_id: 3,
    requester_name: 'Riley Requester',
    department_id: 2,
    department_name: 'IT Department',
    status: 'PENDING_DIRECTOR',
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
    status: 'PENDING_DIRECTOR',
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
      {
        id: 2,
        stage: 'ACCOUNTS',
        decision: 'VERIFIED',
        actor_id: 12,
        reason: '',
        created_at: '2025-01-01T10:00:00Z',
      },
      {
        id: 3,
        stage: 'GM',
        decision: 'RECOMMENDED',
        actor_id: 13,
        reason: '',
        created_at: '2025-01-01T11:00:00Z',
      },
    ],
    processed_by: null,
    processed_at: null,
    purchase_order_number: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T11:00:00Z',
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PurchaseRequestDirectorReviewPage />
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
 * disambiguation the other review page tests use.
 */
function cardHeadingStillInQueue(): boolean {
  return screen.getAllByText('PR-0042').some((el) => el.tagName === 'H3');
}

describe('PurchaseRequestDirectorReviewPage - queue', () => {
  it('shows a loading state before the queue resolves', () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockReturnValue(
      new Promise(() => {})
    );
    renderPage();

    expect(screen.getByText('Pending Requests')).toBeInTheDocument();
    expect(screen.queryByText('PR-0042')).not.toBeInTheDocument();
  });

  it('renders a successful queue with requisition number, requester, department, total and status', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
      queueItem(),
    ]);
    renderPage();

    await screen.findByText('PR-0042');
    expect(screen.getByText(/Riley Requester/)).toBeInTheDocument();
    expect(screen.getByText(/IT Department/)).toBeInTheDocument();
    expect(screen.getByText('$2,400.00')).toBeInTheDocument();
    expect(screen.getByText('Awaiting Director Approval')).toBeInTheDocument();
  });

  it('shows the empty-queue message for a genuinely empty 200 response', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([]);
    renderPage();

    await screen.findByText('No requests waiting for your review.');
    expect(screen.queryByText("You don't have access to this queue")).not.toBeInTheDocument();
  });

  it('shows a distinct access-denied state for a 403, never the empty-queue message', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockRejectedValue({
      response: { status: 403, data: { error: 'Missing required permission', code: 'PERMISSION_DENIED' } },
    });
    renderPage();

    expect(await screen.findByText("You don't have access to this queue")).toBeInTheDocument();
    expect(
      screen.getByText('You do not have access to the Director approval queue.')
    ).toBeInTheDocument();
    expect(screen.queryByText('No requests waiting for your review.')).not.toBeInTheDocument();
  });

  it('never shows the backend\'s raw permission identifier for a 403', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockRejectedValue({
      response: {
        status: 403,
        data: {
          error: "Missing required permission 'procurement.purchase_request.director_approve'",
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
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockRejectedValue(
      new Error('Network Error')
    );
    renderPage();

    await screen.findByText('Failed to load requests awaiting Director approval');
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('retries the queue load when Retry is clicked', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests)
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce([queueItem()]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole('button', { name: /retry/i });

    await user.click(screen.getByRole('button', { name: /retry/i }));

    await screen.findByText('PR-0042');
    expect(purchaseRequestService.getPendingDirectorRequests).toHaveBeenCalledTimes(2);
  });

  it('opens the shared detail view when a request row is clicked', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
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

describe('PurchaseRequestDirectorReviewPage - detail', () => {
  it('shows requester, department, requisition number, items, quantities, unit costs, line totals, category, total and full decision history', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
      queueItem(),
    ]);
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
    // Decision history: Department Head, Accounts, and GM stages are all visible -
    // a newer Director decision (once made) must not hide these earlier ones.
    expect(within(dialog).getByText('Department Head')).toBeInTheDocument();
    expect(within(dialog).getAllByText('Approved').length).toBeGreaterThan(0);
    expect(within(dialog).getByText('Verified')).toBeInTheDocument();
    expect(within(dialog).getByText('Recommended')).toBeInTheDocument();
  });

  it('F22: shows Director reviewer-oriented status copy ("Awaiting Your Approval"), not requester-oriented copy', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Awaiting Your Approval')).toBeInTheDocument();
    expect(within(dialog).getByText('This request requires your approval.')).toBeInTheDocument();
    expect(within(dialog).queryByText(/no action needed/i)).not.toBeInTheDocument();
    // "Awaiting Director Approval" (the objective, requester-oriented label)
    // still legitimately appears twice - the corporate header's status badge
    // and Request Details' own "Current Status" field (see F20's
    // DocumentSection) - it must never appear a THIRD time as the hero's own
    // headline, which is the Director-specific "Awaiting Your Approval" text
    // asserted above instead.
    expect(within(dialog).getAllByText('Awaiting Director Approval')).toHaveLength(2);
  });

  it('renders the detail read-only: no input/textarea controls for editing the request', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
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

  it('shows Approve and Reject only when the request is PENDING_DIRECTOR', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('button', { name: /^approve$/i })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /^reject$/i })).toBeInTheDocument();
  });

  it('hides Approve/Reject when a stale queue row has already moved past PENDING_DIRECTOR', async () => {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      fullRequest({
        status: 'PENDING_PROCUREMENT',
        decisions: [
          { id: 1, stage: 'DEPARTMENT_HEAD', decision: 'APPROVED', actor_id: 11, reason: '', created_at: '2025-01-01T09:00:00Z' },
          { id: 2, stage: 'ACCOUNTS', decision: 'VERIFIED', actor_id: 12, reason: '', created_at: '2025-01-01T10:00:00Z' },
          { id: 3, stage: 'GM', decision: 'RECOMMENDED', actor_id: 13, reason: '', created_at: '2025-01-01T11:00:00Z' },
          { id: 4, stage: 'DIRECTOR', decision: 'APPROVED', actor_id: 14, reason: '', created_at: '2025-01-01T12:00:00Z' },
        ],
      })
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).queryByRole('button', { name: /^approve$/i })).not.toBeInTheDocument();
    expect(within(dialog).queryByRole('button', { name: /^reject$/i })).not.toBeInTheDocument();
  });
});

describe('PurchaseRequestDirectorReviewPage - approve', () => {
  async function openApproveDialog() {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));
    const detailDialog = await screen.findByRole('dialog');
    await user.click(within(detailDialog).getByRole('button', { name: /^approve$/i }));
    return user;
  }

  it('opens a confirmation naming the correct requisition number, with "Approve" wording', async () => {
    await openApproveDialog();

    const dialogs = screen.getAllByRole('dialog');
    const approveDialog = dialogs.find((d) => within(d).queryByText('Approve PR-0042?'));
    expect(approveDialog).toBeTruthy();
    expect(within(approveDialog!).queryByText(/verify/i)).not.toBeInTheDocument();
    expect(within(approveDialog!).queryByText(/recommend/i)).not.toBeInTheDocument();
  });

  it('describes advancing to Procurement, not the GM or Accounts', async () => {
    await openApproveDialog();

    expect(
      screen.getByText('Approving this request will send it to Procurement for processing.')
    ).toBeInTheDocument();
    expect(
      screen.queryByText('This will send the request to the Director for review.')
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText('This will send the request to Accounts for verification.')
    ).not.toBeInTheDocument();
  });

  it('leaves the queue unchanged when cancelled, and does not call approveByDirector', async () => {
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(purchaseRequestService.approveByDirector).not.toHaveBeenCalled();
    expect(cardHeadingStillInQueue()).toBe(true);
  });

  it('calls approveByDirector with the request id on confirm', async () => {
    vi.mocked(purchaseRequestService.approveByDirector).mockResolvedValue(
      fullRequest({ status: 'PENDING_PROCUREMENT' })
    );
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.approveByDirector).toHaveBeenCalledWith(1)
    );
  });

  it('on success: removes the request from the queue, shows a toast, and closes the dialogs', async () => {
    vi.mocked(purchaseRequestService.approveByDirector).mockResolvedValue(
      fullRequest({ status: 'PENDING_PROCUREMENT' })
    );
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('PR-0042'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('on failure: leaves the request in the queue and shows the mapped server error', async () => {
    vi.mocked(purchaseRequestService.approveByDirector).mockRejectedValue({
      response: { data: { error: 'The requester may not act on their own purchase request', code: 'SELF_APPROVAL_FORBIDDEN' } },
    });
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('The requester may not act on their own purchase request')
    );
    expect(cardHeadingStillInQueue()).toBe(true);
  });

  it('disables Approve/Cancel and shows "Approving..." while the request is in flight', async () => {
    let resolveApprove: (value: PurchaseRequest) => void = () => {};
    vi.mocked(purchaseRequestService.approveByDirector).mockReturnValue(
      new Promise((resolve) => {
        resolveApprove = resolve;
      })
    );
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    expect(screen.getByRole('button', { name: /approving/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();

    resolveApprove(fullRequest({ status: 'PENDING_PROCUREMENT' }));
    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
  });
});

describe('PurchaseRequestDirectorReviewPage - reject', () => {
  async function openRejectDialog() {
    vi.mocked(purchaseRequestService.getPendingDirectorRequests).mockResolvedValue([
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

  it('enables Confirm once a valid reason is entered', async () => {
    const user = await openRejectDialog();

    await user.type(
      screen.getByLabelText(/reason/i),
      'Exceeds board-approved capital expenditure limit'
    );

    expect(screen.getByRole('button', { name: /^reject$/i })).toBeEnabled();
  });

  it('calls rejectRequest with the id and trimmed reason on confirm', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED' })
    );
    const user = await openRejectDialog();

    await user.type(
      screen.getByLabelText(/reason/i),
      'Exceeds board-approved capital expenditure limit'
    );
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.rejectRequest).toHaveBeenCalledWith(
        1,
        'Exceeds board-approved capital expenditure limit'
      )
    );
  });

  it('on success: removes the request from the queue, shows a toast, and closes the dialogs', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED' })
    );
    const user = await openRejectDialog();

    await user.type(
      screen.getByLabelText(/reason/i),
      'Exceeds board-approved capital expenditure limit'
    );
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

    await user.type(
      screen.getByLabelText(/reason/i),
      'Exceeds board-approved capital expenditure limit'
    );
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('reason: This field may not be blank.')
    );
    expect(cardHeadingStillInQueue()).toBe(true);
    expect(screen.getByLabelText(/reason/i)).toHaveValue(
      'Exceeds board-approved capital expenditure limit'
    );
    expect(screen.getByRole('button', { name: /^reject$/i })).toBeEnabled();
  });
});
