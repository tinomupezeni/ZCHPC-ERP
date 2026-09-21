import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { toast } from 'sonner';
import type {
  BudgetCode,
  PurchaseRequest,
  PurchaseRequestListItem,
} from '@/types/purchase-request.types';

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
      getBudgetCodes: vi.fn(),
      assignItemBudgetCode: vi.fn(),
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
    ],
    processed_by: null,
    processed_at: null,
    purchase_order_number: null,
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

const BUDGET_CODES: BudgetCode[] = [
  { id: 42, code: 'E-100', name: 'Office Supplies', external_account_type: 'Other Expense' },
  { id: 43, code: 'R-200', name: 'Service Revenue', external_account_type: 'Revenue' },
  { id: 44, code: 'I-300', name: 'Interest Received', external_account_type: 'Other Income' },
];

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(purchaseRequestService.getBudgetCodes).mockResolvedValue(BUDGET_CODES);
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

    expect(await screen.findByText("You don't have access to this queue")).toBeInTheDocument();
    expect(
      screen.getByText('You do not have access to the Accounts verification queue.')
    ).toBeInTheDocument();
    expect(screen.queryByText('No requests waiting for your review.')).not.toBeInTheDocument();
  });

  it('F20 follow-up: never shows the backend\'s raw permission identifier for a 403', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockRejectedValue({
      response: {
        status: 403,
        data: {
          error: "Missing required permission 'procurement.purchase_request.accounts_verify'",
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
    expect(within(dialog).getAllByText('IT Department').length).toBeGreaterThan(0);
    expect(within(dialog).getAllByText('PR-0042').length).toBeGreaterThan(0);
    // "Laptop" now also appears in the F25 budget-code section, so pick the
    // row of the read-only detail table (the one carrying delivery info).
    const itemRow = within(dialog)
      .getAllByText('Laptop')
      .map((el) => el.closest('tr')!)
      .find((row) => within(row).queryByText('Delivery: 2 weeks'))!;
    expect(within(itemRow).getByText('Delivery: 2 weeks')).toBeInTheDocument();
    expect(within(itemRow).getByText('IT Equipment')).toBeInTheDocument();
    const cells = within(itemRow).getAllByRole('cell');
    expect(cells[3]).toHaveTextContent('2'); // Qty
    expect(cells[4]).toHaveTextContent('$1,200.00'); // Unit Cost
    expect(cells[5]).toHaveTextContent('$2,400.00'); // Line Total
    expect(
      within(dialog).getByText('Total Estimated Cost').closest('div')
    ).toHaveTextContent('$2,400.00');
    // Decision history: the earlier Department Head approval is visible.
    expect(within(dialog).getByText('Department Head')).toBeInTheDocument();
    expect(within(dialog).getByText('Approved')).toBeInTheDocument();
  });

  it('F20: shows Accounts reviewer-oriented status copy, not requester-oriented copy', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(fullRequest());
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Awaiting Your Verification')).toBeInTheDocument();
    expect(
      within(dialog).getByText(
        'This request has been approved by the Department Head and requires your budget verification.'
      )
    ).toBeInTheDocument();
    expect(within(dialog).queryByText(/no action needed/i)).not.toBeInTheDocument();
    expect(
      within(dialog).queryByText('Approved by your department head — Accounts is now verifying the budget.')
    ).not.toBeInTheDocument();
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

describe('PurchaseRequestAccountsReviewPage - budget code assignment (F25)', () => {
  const twoItems = (first: number | null, second: number | null): PurchaseRequest =>
    fullRequest({
      items: [
        {
          id: 1,
          description: 'Laptop',
          quantity: 2,
          expected_delivery_period: '2 weeks',
          estimated_cost: '1200.00',
          category_id: 1,
          budget_code_id: first,
          category: { id: 5, name: 'IT Equipment', is_active: true },
        },
        {
          id: 2,
          description: 'Monitor',
          quantity: 1,
          expected_delivery_period: '1 week',
          estimated_cost: '300.00',
          category_id: 2,
          budget_code_id: second,
          category: { id: 6, name: 'Furniture', is_active: true },
        },
      ],
    });

  async function openDetail(request: PurchaseRequest) {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(request);
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));
    const dialog = await screen.findByRole('dialog');
    await within(dialog).findByTestId('budget-code-assignment');
    return { user, dialog };
  }

  it('shows each item with description, quantity, employee category and a selector', async () => {
    const { dialog } = await openDetail(twoItems(null, null));
    const section = within(within(dialog).getByTestId('budget-code-assignment'));

    expect(section.getByText('Laptop')).toBeInTheDocument();
    expect(section.getByText('Monitor')).toBeInTheDocument();
    expect(section.getByText('IT Equipment')).toBeInTheDocument();
    expect(section.getByText('Furniture')).toBeInTheDocument();
    expect(section.getByLabelText('Budget code for Laptop')).toBeInTheDocument();
    expect(section.getByLabelText('Budget code for Monitor')).toBeInTheDocument();
  });

  it('offers exactly the codes the backend returned, and no others', async () => {
    const { dialog } = await openDetail(twoItems(null, null));
    const select = within(dialog).getByLabelText('Budget code for Laptop');

    const options = within(select).getAllByRole('option').map((o) => o.textContent);
    expect(options).toEqual([
      'Select budget code',
      'E-100 — Office Supplies',
      'R-200 — Service Revenue',
      'I-300 — Interest Received',
    ]);
  });

  it('shows the current assignment for an assigned item and "Not assigned" for the other', async () => {
    const { dialog } = await openDetail(twoItems(43, null));
    const section = within(within(dialog).getByTestId('budget-code-assignment'));

    expect(section.getByText('Assigned: R-200 — Service Revenue')).toBeInTheDocument();
    expect(section.getByLabelText('Budget code for Laptop')).toHaveValue('43');
    expect(section.getAllByText('Not assigned')).toHaveLength(1);
  });

  it('assigns a code to one item via the service and reflects the response', async () => {
    const { user, dialog } = await openDetail(twoItems(null, null));
    vi.mocked(purchaseRequestService.assignItemBudgetCode).mockResolvedValue(
      twoItems(42, null)
    );

    await user.selectOptions(
      within(dialog).getByLabelText('Budget code for Laptop'),
      '42'
    );

    expect(purchaseRequestService.assignItemBudgetCode).toHaveBeenCalledWith(1, 1, 42);
    expect(
      await within(dialog).findByText('Assigned: E-100 — Office Supplies')
    ).toBeInTheDocument();
    expect(within(dialog).getAllByText('Not assigned')).toHaveLength(1);
  });

  it('assigns each item independently', async () => {
    const { user, dialog } = await openDetail(twoItems(42, null));
    vi.mocked(purchaseRequestService.assignItemBudgetCode).mockResolvedValue(
      twoItems(42, 44)
    );

    await user.selectOptions(
      within(dialog).getByLabelText('Budget code for Monitor'),
      '44'
    );

    expect(purchaseRequestService.assignItemBudgetCode).toHaveBeenCalledWith(1, 2, 44);
  });

  it('shows the mapped server error and keeps the item unassigned when assignment fails', async () => {
    const { user, dialog } = await openDetail(twoItems(null, null));
    vi.mocked(purchaseRequestService.assignItemBudgetCode).mockRejectedValue({
      response: { data: { error: 'Budget code 9 is not an assignable account' } },
    });

    await user.selectOptions(
      within(dialog).getByLabelText('Budget code for Laptop'),
      '42'
    );

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('Budget code 9 is not an assignable account')
    );
    expect(within(dialog).getAllByText('Not assigned')).toHaveLength(2);
  });

  it('disables Verify until every item has a budget code, and says why', async () => {
    const { dialog } = await openDetail(twoItems(42, null));

    expect(within(dialog).getByRole('button', { name: /^verify$/i })).toBeDisabled();
    expect(
      within(dialog).getByText('Assign a budget code to every item to verify.')
    ).toBeInTheDocument();
  });

  it('enables Verify once every item is assigned, and verification still works', async () => {
    const { user, dialog } = await openDetail(twoItems(42, 43));
    vi.mocked(purchaseRequestService.verifyByAccounts).mockResolvedValue(
      fullRequest({ status: 'PENDING_GM' })
    );

    const verify = within(dialog).getByRole('button', { name: /^verify$/i });
    expect(verify).toBeEnabled();
    await user.click(verify);
    const dialogs = await screen.findAllByRole('dialog');
    const confirm = dialogs.find((d) => within(d).queryByText('Verify PR-0042?'));
    await user.click(within(confirm!).getByRole('button', { name: /^verify$/i }));

    await waitFor(() => expect(purchaseRequestService.verifyByAccounts).toHaveBeenCalledWith(1));
  });

  it('does not show the assignment section when the request is no longer PENDING_ACCOUNTS', async () => {
    vi.mocked(purchaseRequestService.getPendingAccountsRequests).mockResolvedValue([
      queueItem(),
    ]);
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      fullRequest({ status: 'PENDING_GM' })
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByText('PR-0042'));
    await screen.findByRole('dialog');

    expect(screen.queryByTestId('budget-code-assignment')).not.toBeInTheDocument();
  });

  it('shows a load error and offers no codes when the budget-code list cannot be loaded', async () => {
    vi.mocked(purchaseRequestService.getBudgetCodes).mockRejectedValue({
      response: { status: 403, data: { error: 'Forbidden' } },
    });
    const { dialog } = await openDetail(twoItems(null, null));

    expect(await within(dialog).findByRole('alert')).toBeInTheDocument();
    const select = within(dialog).getByLabelText('Budget code for Laptop');
    expect(within(select).getAllByRole('option')).toHaveLength(1);
  });
});
