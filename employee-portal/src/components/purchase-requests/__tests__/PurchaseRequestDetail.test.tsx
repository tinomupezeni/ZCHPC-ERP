import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PurchaseRequestDetail } from '../PurchaseRequestDetail';
import type { PurchaseRequest } from '@/types/purchase-request.types';

function baseRequest(overrides: Partial<PurchaseRequest> = {}): PurchaseRequest {
  return {
    id: 1,
    requisition_number: 'PR-0001',
    requester_id: 1,
    requester_name: 'Richard Matsika',
    department_id: 1,
    department_name: 'IT Department',
    designation: 'Systems Administrator',
    contact: '+263771234567',
    status: 'PENDING_ACCOUNTS',
    total_estimated_cost: '800.00',
    items: [
      {
        id: 1,
        description: 'Laptop',
        quantity: 1,
        expected_delivery_period: '2 weeks',
        estimated_cost: '800.00',
        budget_code_id: 42,
        category: { id: 5, name: 'IT Equipment', is_active: true },
      },
    ],
    decisions: [
      {
        id: 1,
        stage: 'DEPARTMENT_HEAD',
        decision: 'APPROVED',
        actor_id: 9,
        reason: '',
        created_at: '2025-01-02T00:00:00Z',
      },
    ],
    processed_by: null,
    processed_at: null,
    purchase_order_number: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
    ...overrides,
  };
}

describe('PurchaseRequestDetail', () => {
  it('shows requester details from the API', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(screen.getByText('Richard Matsika')).toBeInTheDocument();
    expect(screen.getByText('Systems Administrator')).toBeInTheDocument();
    expect(screen.getByText('+263771234567')).toBeInTheDocument();
    expect(screen.getByText('IT Department')).toBeInTheDocument();
  });

  it('F19: defaults to requester-oriented copy for PENDING_DEPARTMENT_HEAD when no viewerRole is given', () => {
    const request = baseRequest({ status: 'PENDING_DEPARTMENT_HEAD', decisions: [] });
    render(<PurchaseRequestDetail request={request} isOpen onClose={vi.fn()} onEdit={vi.fn()} />);

    // "Awaiting Department Head" appears three times: the status badge, the
    // hero label, and Request Details' objective "Current Status" field -
    // none of them affected by viewerRole here.
    expect(screen.getAllByText('Awaiting Department Head')).toHaveLength(3);
    expect(
      screen.getByText('Submitted — your department head is reviewing it. No action needed from you.')
    ).toBeInTheDocument();
  });

  it('F19: uses requester-oriented copy for PENDING_DEPARTMENT_HEAD when viewerRole="requester" is explicit', () => {
    const request = baseRequest({ status: 'PENDING_DEPARTMENT_HEAD', decisions: [] });
    render(
      <PurchaseRequestDetail
        request={request}
        isOpen
        onClose={vi.fn()}
        onEdit={vi.fn()}
        viewerRole="requester"
      />
    );

    expect(screen.getAllByText('Awaiting Department Head')).toHaveLength(3);
    expect(
      screen.getByText('Submitted — your department head is reviewing it. No action needed from you.')
    ).toBeInTheDocument();
  });

  it('F19: uses reviewer-oriented copy for PENDING_DEPARTMENT_HEAD when viewerRole="department_head"', () => {
    const request = baseRequest({ status: 'PENDING_DEPARTMENT_HEAD', decisions: [] });
    render(
      <PurchaseRequestDetail
        request={request}
        isOpen
        onClose={vi.fn()}
        onEdit={vi.fn()}
        viewerRole="department_head"
      />
    );

    expect(screen.getByText('Awaiting Your Review')).toBeInTheDocument();
    expect(screen.getByText('This request requires your review and approval.')).toBeInTheDocument();
    expect(screen.queryByText(/your department head is reviewing it/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/no action needed/i)).not.toBeInTheDocument();
  });

  it('F19: uses corrected-resubmission copy for a re-submitted PENDING_DEPARTMENT_HEAD request viewed by the department head', () => {
    const request = baseRequest({
      status: 'PENDING_DEPARTMENT_HEAD',
      decisions: [
        {
          id: 1,
          stage: 'DEPARTMENT_HEAD',
          decision: 'REJECTED',
          actor_id: 9,
          reason: 'Please add more detail',
          created_at: '2025-01-02T00:00:00Z',
        },
      ],
    });
    render(
      <PurchaseRequestDetail
        request={request}
        isOpen
        onClose={vi.fn()}
        onEdit={vi.fn()}
        viewerRole="department_head"
      />
    );

    expect(screen.getByText('Correction Requires Your Review')).toBeInTheDocument();
    expect(screen.getByText(/corrected and resubmitted/i)).toBeInTheDocument();
    // Decision history still shows the earlier rejection stage entry.
    expect(screen.getByText('Rejected')).toBeInTheDocument();
  });

  it('shows line items in a table with quantity, delivery period, unit cost and line total as distinct cells', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    const table = screen.getByRole('table');
    expect(within(table).getByText('Description')).toBeInTheDocument();
    expect(within(table).getByText('Qty')).toBeInTheDocument();
    expect(within(table).getByText('Unit Cost')).toBeInTheDocument();
    expect(within(table).getByText('Line Total')).toBeInTheDocument();

    const row = within(table).getByText('Laptop').closest('tr')!;
    expect(within(row).getByText('Delivery: 2 weeks')).toBeInTheDocument();
    expect(within(row).getByText('IT Equipment')).toBeInTheDocument();
    // Unit cost and line total are the same figure here (qty 1) but must
    // still be two distinct cells, not one ambiguous combined string.
    const cells = within(row).getAllByRole('cell');
    expect(cells[3]).toHaveTextContent('1'); // Qty
    expect(cells[4]).toHaveTextContent('$800.00'); // Unit Cost
    expect(cells[5]).toHaveTextContent('$800.00'); // Line Total
  });

  it('shows the total estimated cost in Financial Information and a human-friendly current status', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(screen.getByText('Financial Information')).toBeInTheDocument();
    expect(
      screen.getByText('Total Estimated Cost').closest('div')
    ).toHaveTextContent('$800.00');
    expect(screen.getAllByText('Awaiting Accounts Verification').length).toBeGreaterThan(0);
    expect(screen.queryByText('Pending Accounts')).not.toBeInTheDocument();
  });

  it('shows a status hero explaining what the state means, with no action-implying CTA', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(
      screen.getByText('Approved by your department head — Accounts is now verifying the budget.')
    ).toBeInTheDocument();
    for (const name of [/continue/i, /edit/i, /\bcorrect\b/i, /resubmit/i]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument();
    }
  });

  it('shows a "Not Submitted" hero for a draft, with a "Continue Editing" CTA that opens the editor', async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    render(
      <PurchaseRequestDetail
        request={baseRequest({ status: 'DRAFT', decisions: [] })}
        isOpen
        onClose={vi.fn()}
        onEdit={onEdit}
      />
    );
    expect(screen.getAllByText('Not Submitted').length).toBeGreaterThan(0);
    expect(
      screen.getByText("This request is saved but hasn't been sent for approval yet.")
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /continue editing/i }));
    expect(onEdit).toHaveBeenCalledWith(1);
  });

  it('never renders the raw budget/GL code anywhere', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    // budget_code_id: 42 must never surface as visible text.
    expect(screen.queryByText(/budget_code_id/i)).not.toBeInTheDocument();
    expect(screen.queryByText('42')).not.toBeInTheDocument();
  });

  it('shows the approval workflow read-only, with no approval controls', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(screen.getByText('Approval Workflow')).toBeInTheDocument();
    expect(screen.getByText('Department Head')).toBeInTheDocument();
    expect(screen.getByText('Accounts Verification')).toBeInTheDocument();
    expect(screen.getByText('GM Recommendation')).toBeInTheDocument();
    expect(screen.getByText('Director Approval')).toBeInTheDocument();

    // Only the dialog's own close button may be present - no approve/verify/
    // recommend/reject/process action ever appears in the Employee Portal.
    for (const name of [/approve/i, /verify/i, /recommend/i, /reject/i, /process/i]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument();
    }
  });

  it('marks reached stages as decided and later stages as not reached', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    // Department Head already approved; the request is now pending Accounts.
    const stages = screen.getByText('Approval Workflow').closest('div')!;
    expect(stages).toHaveTextContent('Approved');
    expect(stages).toHaveTextContent('Not Reached');
  });

  it('identifies a rejected request and shows its rejection reason', () => {
    const rejected = baseRequest({
      status: 'REJECTED',
      decisions: [
        {
          id: 2,
          stage: 'ACCOUNTS',
          decision: 'REJECTED',
          actor_id: 5,
          reason: 'Budget code no longer active',
          created_at: '2025-01-03T00:00:00Z',
        },
      ],
    });
    render(<PurchaseRequestDetail request={rejected} isOpen onClose={vi.fn()} onEdit={vi.fn()} />);

    // "Correction Required" is the employee-facing status (badge + hero);
    // "Rejected" is retained only to describe the historical decision event
    // on the Accounts stage row - both must be present, for different reasons.
    expect(screen.getAllByText('Correction Required').length).toBeGreaterThan(0);
    expect(screen.getByText('Budget code no longer active')).toBeInTheDocument();
    expect(screen.getByText('Rejected')).toBeInTheDocument();
    expect(screen.queryByText('Pending Accounts')).not.toBeInTheDocument();
    expect(screen.queryByText('Awaiting Accounts Verification')).not.toBeInTheDocument();
    expect(screen.queryByText('Processed')).not.toBeInTheDocument();
    expect(screen.queryByText('Completed')).not.toBeInTheDocument();
  });

  it('shows a "Review & Correct" CTA for a rejected request that opens the editor', async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    const rejected = baseRequest({
      status: 'REJECTED',
      decisions: [
        {
          id: 2,
          stage: 'ACCOUNTS',
          decision: 'REJECTED',
          actor_id: 5,
          reason: 'Budget code no longer active',
          created_at: '2025-01-03T00:00:00Z',
        },
      ],
    });
    render(<PurchaseRequestDetail request={rejected} isOpen onClose={vi.fn()} onEdit={onEdit} />);

    await user.click(screen.getByRole('button', { name: /review & correct/i }));
    expect(onEdit).toHaveBeenCalledWith(1);
  });

  it('does not render an editing CTA for a non-actionable (waiting) status', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    for (const name of [/continue editing/i, /review & correct/i]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument();
    }
  });

  it('shows procurement info only once actually returned by the API', () => {
    const { rerender } = render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(screen.queryByText('Procurement')).not.toBeInTheDocument();

    rerender(
      <PurchaseRequestDetail
        request={baseRequest({
          status: 'PROCESSED',
          processed_by: 3,
          processed_at: '2025-01-05T00:00:00Z',
          decisions: [
            { id: 1, stage: 'DEPARTMENT_HEAD', decision: 'APPROVED', actor_id: 9, reason: '', created_at: '2025-01-02T00:00:00Z' },
            { id: 2, stage: 'ACCOUNTS', decision: 'VERIFIED', actor_id: 4, reason: '', created_at: '2025-01-02T00:00:00Z' },
            { id: 3, stage: 'GM', decision: 'RECOMMENDED', actor_id: 6, reason: '', created_at: '2025-01-02T00:00:00Z' },
            { id: 4, stage: 'DIRECTOR', decision: 'APPROVED', actor_id: 7, reason: '', created_at: '2025-01-02T00:00:00Z' },
          ],
        })}
        isOpen
        onClose={vi.fn()}
        onEdit={vi.fn()}
      />
    );
    expect(screen.getByText('Procurement')).toBeInTheDocument();
    expect(screen.getByText('Date Processed')).toBeInTheDocument();
    // "Completed" appears twice by design: the status hero, and the
    // Procurement section's own status line.
    expect(screen.getAllByText('Completed').length).toBeGreaterThanOrEqual(2);
  });

  /**
   * F23 follow-up: printing is a Procurement action (see
   * PurchaseRequestProcurementReviewPage's own `actions` slot), never
   * something this shared, role-agnostic component surfaces itself - it has
   * no print link/button for any status or viewerRole, including the
   * default 'requester' view a processed request's own owner would see via
   * PurchaseRequestsPage. This is what keeps printing from becoming a
   * prominent requester-facing action.
   */
  it('never renders a print action itself, for any status or viewer role - printing is a Procurement-page action, not this shared component', () => {
    render(
      <PurchaseRequestDetail
        request={baseRequest({
          status: 'PROCESSED',
          processed_by: 3,
          processed_at: '2025-01-05T00:00:00Z',
          purchase_order_number: 'PO-2026-001',
        })}
        isOpen
        onClose={vi.fn()}
        onEdit={vi.fn()}
        viewerRole="requester"
      />
    );
    expect(screen.queryByRole('link', { name: /print/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /print/i })).not.toBeInTheDocument();
  });
});

describe('PurchaseRequestDetail - line total calculation (regression)', () => {
  // estimated_cost is a per-unit price; the line total is quantity x that
  // unit cost. A prior bug displayed the raw unit cost as if it were
  // already the line total (and the same bug existed server-side in
  // total_estimated_cost), so qty=10 x $1.00 rendered as "$1.00" instead of
  // "$10.00" everywhere this data was shown.
  it('multiplies quantity by unit cost for the line total: qty 10 x $1.00 = $10.00', () => {
    const request = baseRequest({
      total_estimated_cost: '10.00',
      items: [
        {
          id: 1,
          description: 'Widget',
          quantity: 10,
          expected_delivery_period: '1 week',
          estimated_cost: '1.00',
          budget_code_id: 42,
          category: null,
        },
      ],
    });
    render(<PurchaseRequestDetail request={request} isOpen onClose={vi.fn()} onEdit={vi.fn()} />);

    const row = screen.getByText('Widget').closest('tr')!;
    const cells = within(row).getAllByRole('cell');
    expect(cells[cells.length - 2]).toHaveTextContent('$1.00');
    expect(cells[cells.length - 1]).toHaveTextContent('$10.00');
    expect(cells[cells.length - 1]).not.toHaveTextContent('$1.00');
    expect(
      screen.getByText('Total Estimated Cost').closest('div')
    ).toHaveTextContent('$10.00');
  });

  it('computes each line independently across multiple items with different quantities and costs', () => {
    const request = baseRequest({
      total_estimated_cost: '4750.00',
      items: [
        {
          id: 1,
          description: 'Laptop',
          quantity: 2,
          expected_delivery_period: '2 weeks',
          estimated_cost: '2000.00',
          budget_code_id: 42,
          category: null,
        },
        {
          id: 2,
          description: 'Mouse',
          quantity: 5,
          expected_delivery_period: '1 week',
          estimated_cost: '150.00',
          budget_code_id: 42,
          category: null,
        },
      ],
    });
    render(<PurchaseRequestDetail request={request} isOpen onClose={vi.fn()} onEdit={vi.fn()} />);

    const laptopRow = screen.getByText('Laptop').closest('tr')!;
    const laptopCells = within(laptopRow).getAllByRole('cell');
    expect(laptopCells[laptopCells.length - 2]).toHaveTextContent('$2,000.00');
    expect(laptopCells[laptopCells.length - 1]).toHaveTextContent('$4,000.00');

    const mouseRow = screen.getByText('Mouse').closest('tr')!;
    const mouseCells = within(mouseRow).getAllByRole('cell');
    expect(mouseCells[mouseCells.length - 2]).toHaveTextContent('$150.00');
    expect(mouseCells[mouseCells.length - 1]).toHaveTextContent('$750.00');

    expect(
      screen.getByText('Total Estimated Cost').closest('div')
    ).toHaveTextContent('$4,750.00');
  });

  it('renders a $0.00 line total for a zero-cost item without crashing', () => {
    const request = baseRequest({
      total_estimated_cost: '0.00',
      items: [
        {
          id: 1,
          description: 'Free sample',
          quantity: 3,
          expected_delivery_period: '1 week',
          estimated_cost: '0.00',
          budget_code_id: 42,
          category: null,
        },
      ],
    });
    render(<PurchaseRequestDetail request={request} isOpen onClose={vi.fn()} onEdit={vi.fn()} />);

    const row = screen.getByText('Free sample').closest('tr')!;
    const cells = within(row).getAllByRole('cell');
    expect(cells[cells.length - 2]).toHaveTextContent('$0.00');
    expect(cells[cells.length - 1]).toHaveTextContent('$0.00');
  });
});

describe('PurchaseRequestDetail - F20 corporate document structure', () => {
  it('renders the ZCHPC corporate document header with org identity and document title', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(screen.getByAltText('ZCHPC')).toBeInTheDocument();
    expect(
      screen.getByText('Zimbabwe Centre for High Performance Computing')
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Purchase Requisition' })).toBeInTheDocument();
  });

  it('shows a Request Details section with the requisition number, date and objective current status', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    const section = screen.getByText('Request Details').closest('section')!;
    expect(within(section).getByText('PR-0001')).toBeInTheDocument();
    expect(within(section).getByText('Jan 1, 2025')).toBeInTheDocument();
    expect(within(section).getByText('Awaiting Accounts Verification')).toBeInTheDocument();
  });

  it('shows a Financial Information section with the authoritative total', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    const section = screen.getByText('Financial Information').closest('section')!;
    expect(within(section).getByText('Total Estimated Cost')).toBeInTheDocument();
    expect(section).toHaveTextContent('$800.00');
  });

  it('shows Rejection / Correction Context once a rejection has been superseded by a later decision', () => {
    const request = baseRequest({
      status: 'PENDING_ACCOUNTS',
      decisions: [
        {
          id: 1,
          stage: 'DEPARTMENT_HEAD',
          decision: 'REJECTED',
          actor_id: 9,
          reason: 'Wrong model specified',
          created_at: '2025-01-02T00:00:00Z',
        },
        {
          id: 2,
          stage: 'DEPARTMENT_HEAD',
          decision: 'APPROVED',
          actor_id: 9,
          reason: '',
          created_at: '2025-01-03T00:00:00Z',
        },
      ],
    });
    render(<PurchaseRequestDetail request={request} isOpen onClose={vi.fn()} onEdit={vi.fn()} />);

    expect(screen.getByText('Rejection / Correction Context')).toBeInTheDocument();
    expect(screen.getByText(/previously rejected/i)).toBeInTheDocument();
    expect(screen.getByText(/Wrong model specified/)).toBeInTheDocument();
  });

  it('does not show Rejection / Correction Context for a request with no rejection history', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(screen.queryByText('Rejection / Correction Context')).not.toBeInTheDocument();
  });

  it('does not duplicate the correction explanation when the department head hero already covers it', () => {
    const request = baseRequest({
      status: 'PENDING_DEPARTMENT_HEAD',
      decisions: [
        {
          id: 1,
          stage: 'ACCOUNTS',
          decision: 'REJECTED',
          actor_id: 5,
          reason: 'Budget code no longer active',
          created_at: '2025-01-02T00:00:00Z',
        },
      ],
    });
    render(
      <PurchaseRequestDetail
        request={request}
        isOpen
        onClose={vi.fn()}
        onEdit={vi.fn()}
        viewerRole="department_head"
      />
    );

    // The hero already says this ("Correction Requires Your Review" / ".
    // ..corrected and resubmitted...") - the separate section would repeat it.
    expect(screen.queryByText('Rejection / Correction Context')).not.toBeInTheDocument();
    expect(screen.getByText('Correction Requires Your Review')).toBeInTheDocument();
  });

  it('F20: uses Accounts reviewer-oriented copy for PENDING_ACCOUNTS when viewerRole="accounts"', () => {
    const request = baseRequest({ status: 'PENDING_ACCOUNTS' });
    render(
      <PurchaseRequestDetail
        request={request}
        isOpen
        onClose={vi.fn()}
        onEdit={vi.fn()}
        viewerRole="accounts"
      />
    );

    expect(screen.getByText('Awaiting Your Verification')).toBeInTheDocument();
    expect(
      screen.getByText(
        'This request has been approved by the Department Head and requires your budget verification.'
      )
    ).toBeInTheDocument();
    expect(screen.queryByText(/no action needed/i)).not.toBeInTheDocument();
  });

  it('leaves the requester\'s own PENDING_ACCOUNTS copy unaffected by the accounts viewer role', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(
      screen.getByText('Approved by your department head — Accounts is now verifying the budget.')
    ).toBeInTheDocument();
    expect(screen.queryByText('Awaiting Your Verification')).not.toBeInTheDocument();
  });
});
