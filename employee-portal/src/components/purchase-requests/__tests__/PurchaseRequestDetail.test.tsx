import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
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
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} />
    );
    expect(screen.getByText('Richard Matsika')).toBeInTheDocument();
    expect(screen.getByText('Systems Administrator')).toBeInTheDocument();
    expect(screen.getByText('+263771234567')).toBeInTheDocument();
    expect(screen.getByText('IT Department')).toBeInTheDocument();
  });

  it('shows line items with quantity, delivery period and cost', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} />
    );
    expect(screen.getByText('Laptop')).toBeInTheDocument();
    expect(screen.getByText('Qty: 1')).toBeInTheDocument();
    expect(screen.getByText('Delivery: 2 weeks')).toBeInTheDocument();
    expect(screen.getByText('Cost: $800.00')).toBeInTheDocument();
  });

  it('shows the total estimated cost and a human-friendly current status', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} />
    );
    expect(screen.getByText('$800.00')).toBeInTheDocument();
    expect(screen.getAllByText('Awaiting Accounts Verification').length).toBeGreaterThan(0);
    expect(screen.queryByText('Pending Accounts')).not.toBeInTheDocument();
  });

  it('shows a status hero explaining what the state means, with no action-implying CTA', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} />
    );
    expect(
      screen.getByText('Approved by your department head — Accounts is now verifying the budget.')
    ).toBeInTheDocument();
    for (const name of [/continue/i, /edit/i, /\bcorrect\b/i, /resubmit/i]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument();
    }
  });

  it('shows a "Not Submitted" hero for a draft, with no editing CTA', () => {
    render(
      <PurchaseRequestDetail request={baseRequest({ status: 'DRAFT', decisions: [] })} isOpen onClose={vi.fn()} />
    );
    expect(screen.getAllByText('Not Submitted').length).toBeGreaterThan(0);
    expect(
      screen.getByText("This request is saved but hasn't been sent for approval yet.")
    ).toBeInTheDocument();
    for (const name of [/continue/i, /edit/i]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument();
    }
  });

  it('never renders the raw budget/GL code anywhere', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} />
    );
    // budget_code_id: 42 must never surface as visible text.
    expect(screen.queryByText(/budget_code_id/i)).not.toBeInTheDocument();
    expect(screen.queryByText('42')).not.toBeInTheDocument();
  });

  it('shows the approval workflow read-only, with no approval controls', () => {
    render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} />
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
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} />
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
    render(<PurchaseRequestDetail request={rejected} isOpen onClose={vi.fn()} />);

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

  it('does not render any editing/correction/resubmission CTA for a rejected request', () => {
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
    render(<PurchaseRequestDetail request={rejected} isOpen onClose={vi.fn()} />);

    for (const name of [/continue/i, /edit/i, /\bcorrect\b/i, /resubmit/i]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument();
    }
  });

  it('shows procurement info only once actually returned by the API', () => {
    const { rerender } = render(
      <PurchaseRequestDetail request={baseRequest()} isOpen onClose={vi.fn()} />
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
      />
    );
    expect(screen.getByText('Procurement')).toBeInTheDocument();
    expect(screen.getByText('Date Processed')).toBeInTheDocument();
    // "Completed" appears twice by design: the status hero, and the
    // Procurement section's own status line.
    expect(screen.getAllByText('Completed').length).toBeGreaterThanOrEqual(2);
  });
});
