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
      getPendingProcurementRequests: vi.fn(),
      getRequest: vi.fn(),
      processRequest: vi.fn(),
    },
  };
});

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { PurchaseRequestProcurementReviewPage } = await import(
  '../PurchaseRequestProcurementReviewPage'
);

function queueItem(overrides: Partial<PurchaseRequestListItem> = {}): PurchaseRequestListItem {
  return {
    id: 1,
    requisition_number: 'PR-0042',
    requester_id: 3,
    requester_name: 'Riley Requester',
    department_id: 2,
    department_name: 'IT Department',
    status: 'PENDING_PROCUREMENT',
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
    status: 'PENDING_PROCUREMENT',
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
        budget_code: null,
        category: { id: 5, name: 'IT Equipment', is_active: true },
      },
    ],
    decisions: [
      { id: 1, stage: 'DEPARTMENT_HEAD', decision: 'APPROVED', actor_id: 11, reason: '', created_at: '2025-01-01T09:00:00Z' },
      { id: 2, stage: 'ACCOUNTS', decision: 'VERIFIED', actor_id: 12, reason: '', created_at: '2025-01-01T10:00:00Z' },
      { id: 3, stage: 'GM', decision: 'RECOMMENDED', actor_id: 13, reason: '', created_at: '2025-01-01T11:00:00Z' },
      { id: 4, stage: 'DIRECTOR', decision: 'APPROVED', actor_id: 14, reason: '', created_at: '2025-01-01T12:00:00Z' },
    ],
    processed_by: null,
    processed_at: null,
    purchase_order_number: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T12:00:00Z',
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PurchaseRequestProcurementReviewPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

function cardHeadingStillInQueue(): boolean {
  return screen.getAllByText('PR-0042').some((el) => el.tagName === 'H3');
}

describe('PurchaseRequestProcurementReviewPage - queue', () => {
  it('shows a loading state before the queue resolves', () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockReturnValue(
      new Promise(() => {})
    );
    renderPage();

    expect(screen.getByText('Pending Requests')).toBeInTheDocument();
    expect(screen.queryByText('PR-0042')).not.toBeInTheDocument();
  });

  it('renders a successful queue with requisition number, requester, department, total and status', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([
      queueItem(),
    ]);
    renderPage();

    await screen.findByText('PR-0042');
    expect(screen.getByText(/Riley Requester/)).toBeInTheDocument();
    expect(screen.getByText(/IT Department/)).toBeInTheDocument();
    expect(screen.getByText('$2,400.00')).toBeInTheDocument();
    expect(screen.getByText('Being Processed')).toBeInTheDocument();
  });

  it('shows the empty-queue message for a genuinely empty 200 response', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([]);
    renderPage();

    await screen.findByText('No requests waiting for your review.');
    expect(screen.queryByText("You don't have access to this queue")).not.toBeInTheDocument();
  });

  it('shows a distinct access-denied state for a 403, never the empty-queue message', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockRejectedValue({
      response: { status: 403, data: { error: 'Missing required permission', code: 'PERMISSION_DENIED' } },
    });
    renderPage();

    expect(await screen.findByText("You don't have access to this queue")).toBeInTheDocument();
    expect(
      screen.getByText('You do not have access to the Procurement processing queue.')
    ).toBeInTheDocument();
    expect(screen.queryByText('No requests waiting for your review.')).not.toBeInTheDocument();
  });

  it('opens the shared detail view when a request row is clicked', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([
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

describe('PurchaseRequestProcurementReviewPage - detail', () => {
  it('shows the complete approval history through Director approval', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Department Head')).toBeInTheDocument();
    expect(within(dialog).getByText('Verified')).toBeInTheDocument();
    expect(within(dialog).getByText('Recommended')).toBeInTheDocument();
    expect(within(dialog).getAllByText('Approved').length).toBeGreaterThan(0);
  });

  it('F23: shows Procurement reviewer-oriented status copy ("Awaiting Processing")', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Awaiting Processing')).toBeInTheDocument();
    expect(
      within(dialog).getByText('This request is ready for procurement processing.')
    ).toBeInTheDocument();
  });

  it('shows Process (and neither Reject nor Print) when the request is PENDING_PROCUREMENT', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('button', { name: /^process$/i })).toBeInTheDocument();
    expect(within(dialog).queryByRole('button', { name: /^reject$/i })).not.toBeInTheDocument();
    expect(
      within(dialog).queryByRole('link', { name: /print requisition/i })
    ).not.toBeInTheDocument();
  });

  it('hides Process (and shows Print Requisition instead) once the request is PROCESSED', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      fullRequest({ status: 'PROCESSED', purchase_order_number: 'PO-1' })
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).queryByRole('button', { name: /^process$/i })).not.toBeInTheDocument();
    expect(within(dialog).getByRole('link', { name: /print requisition/i })).toBeInTheDocument();
  });

  it('shows a Print Requisition action, navigating to the existing standalone print route, once the request is PROCESSED', async () => {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      fullRequest({
        status: 'PROCESSED',
        purchase_order_number: 'PO-2026-777',
        processed_at: '2025-01-02T09:00:00Z',
      })
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('PO-2026-777')).toBeInTheDocument();
    const printLink = within(dialog).getByRole('link', { name: /print requisition/i });
    expect(printLink).toHaveAttribute('href', '/portal/purchase-requests/1/print');
    expect(printLink).toHaveAttribute('target', '_blank');
    expect(printLink).toHaveAttribute('rel', expect.stringContaining('noopener'));
  });
});

describe('PurchaseRequestProcurementReviewPage - process', () => {
  async function openProcessDialog() {
    vi.mocked(purchaseRequestService.getPendingProcurementRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));
    const detailDialog = await screen.findByRole('dialog');
    await user.click(within(detailDialog).getByRole('button', { name: /^process$/i }));
    return user;
  }

  it('opens a dialog naming the correct requisition number', async () => {
    await openProcessDialog();

    expect(screen.getByText('Process PR-0042')).toBeInTheDocument();
  });

  it('keeps Confirm disabled for a blank PO number', async () => {
    await openProcessDialog();

    expect(screen.getByRole('button', { name: /^process$/i })).toBeDisabled();
  });

  it('enables Confirm once a PO number is entered', async () => {
    const user = await openProcessDialog();

    await user.type(screen.getByLabelText(/purchase order number/i), 'PO-2026-00042');

    expect(screen.getByRole('button', { name: /^process$/i })).toBeEnabled();
  });

  it('calls processRequest with the id and trimmed PO number on confirm', async () => {
    vi.mocked(purchaseRequestService.processRequest).mockResolvedValue(
      fullRequest({ status: 'PROCESSED', purchase_order_number: 'PO-2026-00042' })
    );
    const user = await openProcessDialog();

    await user.type(screen.getByLabelText(/purchase order number/i), '  PO-2026-00042  ');
    await user.click(screen.getByRole('button', { name: /^process$/i }));

    await waitFor(() =>
      expect(purchaseRequestService.processRequest).toHaveBeenCalledWith(1, 'PO-2026-00042')
    );
  });

  it('on success: removes the request from the queue, shows a toast, and keeps the detail open now offering Print Requisition', async () => {
    vi.mocked(purchaseRequestService.processRequest).mockResolvedValue(
      fullRequest({ status: 'PROCESSED', purchase_order_number: 'PO-2026-00042' })
    );
    const user = await openProcessDialog();

    await user.type(screen.getByLabelText(/purchase order number/i), 'PO-2026-00042');
    await user.click(screen.getByRole('button', { name: /^process$/i }));

    await waitFor(() =>
      expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('PR-0042'))
    );
    // The dialog is deliberately NOT closed - a processed request leaves the
    // pending-procurement scope immediately, so staying open with Print
    // Requisition is the only way to get from Process straight to Print.
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByRole('link', { name: /print requisition/i })).toBeInTheDocument();
    expect(within(dialog).queryByRole('button', { name: /^process$/i })).not.toBeInTheDocument();
    // Removed from the queue behind the dialog, not merely visually hidden.
    expect(cardHeadingStillInQueue()).toBe(false);
  });

  it('on failure (e.g. duplicate PO number): leaves the request in the queue, shows the mapped server error, and the PO number is retryable', async () => {
    vi.mocked(purchaseRequestService.processRequest).mockRejectedValue({
      response: {
        status: 409,
        data: { error: "Purchase order number 'PO-2026-00042' is already in use", code: 'PO_NUMBER_ALREADY_EXISTS' },
      },
    });
    const user = await openProcessDialog();

    await user.type(screen.getByLabelText(/purchase order number/i), 'PO-2026-00042');
    await user.click(screen.getByRole('button', { name: /^process$/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Purchase order number 'PO-2026-00042' is already in use")
    );
    expect(cardHeadingStillInQueue()).toBe(true);
    expect(screen.getByLabelText(/purchase order number/i)).toHaveValue('PO-2026-00042');
  });

  it('disables Process/Cancel and shows "Processing..." while the request is in flight', async () => {
    let resolveProcess: (value: PurchaseRequest) => void = () => {};
    vi.mocked(purchaseRequestService.processRequest).mockReturnValue(
      new Promise((resolve) => {
        resolveProcess = resolve;
      })
    );
    const user = await openProcessDialog();
    await user.type(screen.getByLabelText(/purchase order number/i), 'PO-2026-00042');

    await user.click(screen.getByRole('button', { name: /^process$/i }));

    expect(screen.getByRole('button', { name: /processing/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();

    resolveProcess(fullRequest({ status: 'PROCESSED', purchase_order_number: 'PO-2026-00042' }));
    await waitFor(() =>
      expect(screen.getByRole('link', { name: /print requisition/i })).toBeInTheDocument()
    );
  });

  it('leaves the queue unchanged when cancelled, and does not call processRequest', async () => {
    const user = await openProcessDialog();

    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(purchaseRequestService.processRequest).not.toHaveBeenCalled();
    expect(cardHeadingStillInQueue()).toBe(true);
  });
});
