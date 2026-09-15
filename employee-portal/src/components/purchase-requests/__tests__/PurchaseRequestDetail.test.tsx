import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
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

  it('shows line items with quantity, delivery period, unit cost and line total', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(screen.getByText('Laptop')).toBeInTheDocument();
    expect(screen.getByText('Qty: 1')).toBeInTheDocument();
    expect(screen.getByText('Delivery: 2 weeks')).toBeInTheDocument();
    expect(screen.getByText('Unit Cost: $800.00')).toBeInTheDocument();
    expect(screen.getByText('Line Total: $800.00')).toBeInTheDocument();
  });

  it('shows the total estimated cost and a human-friendly current status', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} onEdit={vi.fn()} />
    );
    expect(screen.getByText('$800.00')).toBeInTheDocument();
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

    expect(screen.getByText('Unit Cost: $1.00')).toBeInTheDocument();
    expect(screen.getByText('Line Total: $10.00')).toBeInTheDocument();
    expect(screen.queryByText('Line Total: $1.00')).not.toBeInTheDocument();
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

    expect(screen.getByText('Unit Cost: $2,000.00')).toBeInTheDocument();
    expect(screen.getByText('Line Total: $4,000.00')).toBeInTheDocument();
    expect(screen.getByText('Unit Cost: $150.00')).toBeInTheDocument();
    expect(screen.getByText('Line Total: $750.00')).toBeInTheDocument();
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

    expect(screen.getByText('Unit Cost: $0.00')).toBeInTheDocument();
    expect(screen.getByText('Line Total: $0.00')).toBeInTheDocument();
  });
});
