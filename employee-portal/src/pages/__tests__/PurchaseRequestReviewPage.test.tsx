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
      getPendingDepartmentHeadRequests: vi.fn(),
      getRequest: vi.fn(),
      approveByDepartmentHead: vi.fn(),
      rejectRequest: vi.fn(),
    },
  };
});

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { PurchaseRequestReviewPage } = await import('../PurchaseRequestReviewPage');

function queueItem(overrides: Partial<PurchaseRequestListItem> = {}): PurchaseRequestListItem {
  return {
    id: 1,
    requisition_number: 'PR-0042',
    requester_id: 3,
    requester_name: 'Jane Moyo',
    department_id: 2,
    department_name: 'IT Department',
    status: 'PENDING_DEPARTMENT_HEAD',
    total_estimated_cost: '1200.00',
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
    requester_name: 'Jane Moyo',
    department_id: 2,
    department_name: 'IT Department',
    designation: 'Technician',
    contact: '+263771111111',
    status: 'PENDING_DEPARTMENT_HEAD',
    total_estimated_cost: '1200.00',
    items: [
      {
        id: 1,
        description: 'Laptop',
        quantity: 1,
        expected_delivery_period: '2 weeks',
        estimated_cost: '1200.00',
        category_id: 1,
        budget_code_id: 42,
        budget_code: null,
        category: { id: 5, name: 'IT Equipment', is_active: true },
      },
    ],
    decisions: [],
    processed_by: null,
    processed_at: null,
    purchase_order_number: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PurchaseRequestReviewPage />
    </MemoryRouter>
  );
}

function renderPageAtPath(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <PurchaseRequestReviewPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

/**
 * With the detail dialog open, Radix marks the rest of the page
 * aria-hidden for screen readers - so getByRole can no longer see the
 * queue card's heading behind the modal, even though it's still in the
 * DOM. getByText isn't accessibility-tree-filtered, but "PR-0042" also
 * appears verbatim in the (still-open) dialog's own title - so this
 * disambiguates by checking specifically for the card's <h3>, the one
 * PurchaseRequestReviewCard actually renders.
 */
function cardHeadingStillInQueue(): boolean {
  return screen.getAllByText('PR-0042').some((el) => el.tagName === 'H3');
}

describe('PurchaseRequestReviewPage - queue authorization', () => {
  it('shows a distinct access-denied state for a 403, never the empty-queue message', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockRejectedValue({
      response: { status: 403, data: { error: 'Missing required permission', code: 'PERMISSION_DENIED' } },
    });
    renderPage();

    expect(await screen.findByText("You don't have access to this queue")).toBeInTheDocument();
    expect(
      screen.getByText('You do not have access to the department-head review queue.')
    ).toBeInTheDocument();
    expect(screen.queryByText('No requests waiting for your review.')).not.toBeInTheDocument();
  });

  it('F20 follow-up: never shows the backend\'s raw permission identifier for a 403', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockRejectedValue({
      response: {
        status: 403,
        data: {
          error: "Missing required permission 'procurement.purchase_request.department_head_approve'",
          code: 'PERMISSION_DENIED',
        },
      },
    });
    renderPage();

    await screen.findByText("You don't have access to this queue");
    expect(screen.queryByText(/missing required permission/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/procurement\.purchase_request/i)).not.toBeInTheDocument();
  });

  it('shows the empty-queue message for a genuinely empty 200 response', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([]);
    renderPage();

    await screen.findByText('No requests waiting for your review.');
    expect(screen.queryByText("You don't have access to this queue")).not.toBeInTheDocument();
  });

  it('shows a generic error state (with retry) for a non-403 failure', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockRejectedValue(
      new Error('Network Error')
    );
    renderPage();

    await screen.findByText('Failed to load requests awaiting your review');
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});

describe('PurchaseRequestReviewPage - detail and review actions', () => {
  it('opens the shared detail view showing requester, items and total, with Approve/Reject for a pending review', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Jane Moyo')).toBeInTheDocument();
    const itemRow = within(dialog).getByText('Laptop').closest('tr')!;
    const cells = within(itemRow).getAllByRole('cell');
    expect(cells[4]).toHaveTextContent('$1,200.00'); // Unit Cost
    expect(within(dialog).getByRole('button', { name: /^approve$/i })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /^reject$/i })).toBeInTheDocument();
  });

  it('does not show Approve/Reject when the request is no longer PENDING_DEPARTMENT_HEAD', async () => {
    // The queue row was fetched before someone else already decided it -
    // the detail fetch reveals a status the review actions must not act on.
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED', decisions: [
        { id: 1, stage: 'DEPARTMENT_HEAD', decision: 'REJECTED', actor_id: 9, reason: 'Already handled', created_at: '2025-01-02T00:00:00Z' },
      ] })
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).queryByRole('button', { name: /^approve$/i })).not.toBeInTheDocument();
    expect(within(dialog).queryByRole('button', { name: /^reject$/i })).not.toBeInTheDocument();
  });

  it('F19 follow-up: uses reviewer-oriented status copy, never the requester wording, for a first-time PENDING_DEPARTMENT_HEAD request', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Awaiting Your Review')).toBeInTheDocument();
    expect(
      within(dialog).getByText('This request requires your review and approval.')
    ).toBeInTheDocument();
    expect(within(dialog).queryByText(/no action needed/i)).not.toBeInTheDocument();
    expect(within(dialog).queryByText(/your department head is reviewing/i)).not.toBeInTheDocument();
  });

  it('F19 follow-up: uses corrected-resubmission copy when the request already carries decision history', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      fullRequest({
        status: 'PENDING_DEPARTMENT_HEAD',
        decisions: [
          { id: 1, stage: 'DEPARTMENT_HEAD', decision: 'APPROVED', actor_id: 9, reason: '', created_at: '2025-01-02T00:00:00Z' },
          { id: 2, stage: 'ACCOUNTS', decision: 'REJECTED', actor_id: 12, reason: 'Category needs revisiting', created_at: '2025-01-03T00:00:00Z' },
        ],
      })
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Correction Requires Your Review')).toBeInTheDocument();
    expect(within(dialog).getByText(/corrected and resubmitted/i)).toBeInTheDocument();
    // Decision history (including the earlier rejection) remains visible alongside the new copy.
    expect(within(dialog).getByText('Rejected')).toBeInTheDocument();
  });

  it('handles the detail fetch failing (e.g. the request vanished) without corrupting the queue', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockRejectedValue({
      response: { data: { error: 'Purchase request 1 not found' } },
    });
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('Purchase request 1 not found')
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    // The queue itself is untouched by a detail-fetch failure.
    expect(screen.getByText('PR-0042')).toBeInTheDocument();
  });
});

describe('PurchaseRequestReviewPage - F19 notification deep link', () => {
  it('opens the detail for the requestId in the query string on mount (a "Purchase Request Corrected" notification link)', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());

    renderPageAtPath('/portal/purchase-requests/review?requestId=1&action=view');

    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(purchaseRequestService.getRequest).toHaveBeenCalledWith(1);
  });

  it('does not open any detail when there is no requestId in the query string', async () => {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([]);

    renderPageAtPath('/portal/purchase-requests/review');

    await screen.findByText('No requests waiting for your review.');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(purchaseRequestService.getRequest).not.toHaveBeenCalled();
  });
});

describe('PurchaseRequestReviewPage - approve', () => {
  async function openApproveDialog() {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([
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

  it('opens a confirmation naming the correct requisition number', async () => {
    await openApproveDialog();

    const dialogs = screen.getAllByRole('dialog');
    const approveDialog = dialogs.find((d) => within(d).queryByText('Approve PR-0042?'));
    expect(approveDialog).toBeTruthy();
  });

  it('leaves the queue unchanged when the approval is cancelled', async () => {
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(purchaseRequestService.approveByDepartmentHead).not.toHaveBeenCalled();
    expect(cardHeadingStillInQueue()).toBe(true);
  });

  it('calls approveByDepartmentHead with the request id on confirm', async () => {
    vi.mocked(purchaseRequestService.approveByDepartmentHead).mockResolvedValue(
      fullRequest({ status: 'PENDING_ACCOUNTS' })
    );
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.approveByDepartmentHead).toHaveBeenCalledWith(1)
    );
  });

  it('on success: removes the request from the queue, shows a toast, and closes the dialogs', async () => {
    vi.mocked(purchaseRequestService.approveByDepartmentHead).mockResolvedValue(
      fullRequest({ status: 'PENDING_ACCOUNTS' })
    );
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('PR-0042'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('on failure: leaves the request in the queue and shows the mapped server error', async () => {
    vi.mocked(purchaseRequestService.approveByDepartmentHead).mockRejectedValue({
      response: { data: { error: 'The actor is not the recorded head of this department', code: 'DEPARTMENT_CONTEXT_DENIED' } },
    });
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('The actor is not the recorded head of this department')
    );
    expect(cardHeadingStillInQueue()).toBe(true);
  });

  it('disables Approve/Cancel while the request is in flight', async () => {
    let resolveApprove: (value: PurchaseRequest) => void = () => {};
    vi.mocked(purchaseRequestService.approveByDepartmentHead).mockReturnValue(
      new Promise((resolve) => {
        resolveApprove = resolve;
      })
    );
    const user = await openApproveDialog();

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    expect(screen.getByRole('button', { name: /approving/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();

    resolveApprove(fullRequest({ status: 'PENDING_ACCOUNTS' }));
    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
  });
});

describe('PurchaseRequestReviewPage - reject', () => {
  async function openRejectDialog() {
    vi.mocked(purchaseRequestService.getPendingDepartmentHeadRequests).mockResolvedValue([
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

  it('keeps Confirm disabled for a blank reason and enables it once text is entered', async () => {
    const user = await openRejectDialog();

    const confirmButton = screen.getByRole('button', { name: /^reject$/i });
    expect(confirmButton).toBeDisabled();

    await user.type(screen.getByLabelText(/reason/i), 'Budget code no longer active');
    expect(confirmButton).toBeEnabled();
  });

  it('calls rejectRequest with the id and trimmed reason on confirm', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED' })
    );
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Budget code no longer active');
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.rejectRequest).toHaveBeenCalledWith(
        1,
        'Budget code no longer active'
      )
    );
  });

  it('on success: removes the request from the queue, shows a toast, and closes the dialogs', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockResolvedValue(
      fullRequest({ status: 'REJECTED' })
    );
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Budget code no longer active');
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('PR-0042'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('on failure: leaves the request in the queue, shows the mapped server error, and preserves the typed reason', async () => {
    vi.mocked(purchaseRequestService.rejectRequest).mockRejectedValue({
      response: { data: { error: 'reason: This field may not be blank.' } },
    });
    const user = await openRejectDialog();

    await user.type(screen.getByLabelText(/reason/i), 'Budget code no longer active');
    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('reason: This field may not be blank.')
    );
    expect(cardHeadingStillInQueue()).toBe(true);
    // Dialog state is recoverable: the reason the reviewer already typed is
    // still there, not wiped out by the failed attempt.
    expect(screen.getByLabelText(/reason/i)).toHaveValue('Budget code no longer active');
  });

  it('disables the reason field and buttons while the request is in flight', async () => {
    let resolveReject: (value: PurchaseRequest) => void = () => {};
    vi.mocked(purchaseRequestService.rejectRequest).mockReturnValue(
      new Promise((resolve) => {
        resolveReject = resolve;
      })
    );
    const user = await openRejectDialog();
    await user.type(screen.getByLabelText(/reason/i), 'Budget code no longer active');

    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    expect(screen.getByLabelText(/reason/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /rejecting/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();

    resolveReject(fullRequest({ status: 'REJECTED' }));
    await waitFor(() => expect(screen.queryByText('PR-0042')).not.toBeInTheDocument());
  });
});
