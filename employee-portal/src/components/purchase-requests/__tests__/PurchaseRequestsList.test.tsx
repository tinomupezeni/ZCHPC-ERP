import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PurchaseRequestsList } from '../PurchaseRequestsList';
import type { PurchaseRequestListItem } from '@/types/purchase-request.types';

const requests: PurchaseRequestListItem[] = [
  {
    id: 1,
    requisition_number: 'PR-0001',
    requester_id: 1,
    requester_name: 'Richard Matsika',
    department_id: 1,
    department_name: 'IT Department',
    status: 'PENDING_DEPARTMENT_HEAD',
    total_estimated_cost: '800.00',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    requisition_number: 'PR-0002',
    requester_id: 1,
    requester_name: 'Richard Matsika',
    department_id: 1,
    department_name: 'IT Department',
    status: 'REJECTED',
    total_estimated_cost: '150.00',
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

function baseProps() {
  return {
    requests,
    isLoading: false,
    error: null,
    onRetry: vi.fn(),
    onView: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    bucketFilter: 'all' as const,
    onBucketFilterChange: vi.fn(),
  };
}

describe('PurchaseRequestsList', () => {
  it('shows a loading state', () => {
    render(<PurchaseRequestsList {...baseProps()} isLoading requests={[]} />);
    expect(screen.getByText('My Purchase Requests')).toBeInTheDocument();
    expect(screen.queryByText('PR-0001')).not.toBeInTheDocument();
  });

  it('shows an empty state when there are no requests at all', () => {
    render(<PurchaseRequestsList {...baseProps()} requests={[]} />);
    expect(screen.getByText('No purchase requests found')).toBeInTheDocument();
  });

  it('shows an error state with a working retry action', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(
      <PurchaseRequestsList
        {...baseProps()}
        requests={[]}
        error="Failed to load your purchase requests"
        onRetry={onRetry}
      />
    );

    expect(screen.getByText('Failed to load your purchase requests')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders human-readable, action-oriented statuses, not raw enum strings or bare "Draft"/"Rejected"', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    expect(screen.getByText('Awaiting Department Head')).toBeInTheDocument();
    expect(screen.getByText('Correction Required')).toBeInTheDocument();
    expect(screen.queryByText('PENDING_DEPARTMENT_HEAD')).not.toBeInTheDocument();
    expect(screen.queryByText('Pending Department Head')).not.toBeInTheDocument();
  });

  it('shows the requisition number, department, date and total on each card', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    expect(screen.getByText('PR-0001')).toBeInTheDocument();
    expect(screen.getByText('$800.00')).toBeInTheDocument();
    expect(screen.getByText('PR-0002')).toBeInTheDocument();
    expect(screen.getByText('$150.00')).toBeInTheDocument();
    expect(screen.getAllByText('IT Department')).toHaveLength(2);
  });

  it('shows a plain-language explanation for a waiting request, including "no action needed"', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    expect(
      screen.getByText(/your department head is reviewing it/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/no action needed from you/i)).toBeInTheDocument();
  });

  it('shows a "Review & Correct" CTA on a rejected request card that opens the editor without opening the detail view', async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    const onView = vi.fn();
    render(<PurchaseRequestsList {...baseProps()} onEdit={onEdit} onView={onView} />);

    // Exact-anchored: the card itself also has role="button" and its
    // accessible name is derived from all of its text content (including
    // this CTA's own label), so an unanchored match would be ambiguous.
    await user.click(screen.getByRole('button', { name: /^review & correct$/i }));
    expect(onEdit).toHaveBeenCalledWith(2);
    expect(onView).not.toHaveBeenCalled();
  });

  it('does not render an editing CTA for a waiting (non-actionable) request', () => {
    const waitingOnly: PurchaseRequestListItem[] = [requests[0]];
    render(<PurchaseRequestsList {...baseProps()} requests={waitingOnly} />);
    for (const name of [/continue/i, /review & correct/i]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument();
    }
  });

  describe('Delete Draft (Slice 4)', () => {
    const draftItem: PurchaseRequestListItem = {
      ...requests[0],
      id: 3,
      requisition_number: 'PR-0003',
      status: 'DRAFT',
    };

    it('shows a Delete Draft CTA only for a DRAFT request', () => {
      render(<PurchaseRequestsList {...baseProps()} requests={[draftItem]} />);
      expect(screen.getByRole('button', { name: /^delete draft$/i })).toBeInTheDocument();
    });

    it('does not show Delete Draft for REJECTED, PENDING_*, or PROCESSED requests', () => {
      const nonDraft: PurchaseRequestListItem[] = [
        requests[0], // PENDING_DEPARTMENT_HEAD
        requests[1], // REJECTED
        { ...requests[0], id: 4, requisition_number: 'PR-0004', status: 'PROCESSED' },
      ];
      render(<PurchaseRequestsList {...baseProps()} requests={nonDraft} />);
      expect(screen.queryByRole('button', { name: /delete draft/i })).not.toBeInTheDocument();
    });

    it('calls onDelete with the request id without opening the detail view', async () => {
      const user = userEvent.setup();
      const onDelete = vi.fn();
      const onView = vi.fn();
      render(
        <PurchaseRequestsList
          {...baseProps()}
          requests={[draftItem]}
          onDelete={onDelete}
          onView={onView}
        />
      );

      await user.click(screen.getByRole('button', { name: /^delete draft$/i }));

      expect(onDelete).toHaveBeenCalledWith(3);
      expect(onView).not.toHaveBeenCalled();
    });
  });

  it('opens the request detail when a card is clicked', async () => {
    const user = userEvent.setup();
    const onView = vi.fn();
    render(<PurchaseRequestsList {...baseProps()} onView={onView} />);

    await user.click(screen.getByText('PR-0001'));
    expect(onView).toHaveBeenCalledWith(1);
  });

  it('shows a "needs your attention" banner when action-required requests exist', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    expect(screen.getByText(/need.*your attention/i)).toBeInTheDocument();
  });

  it('does not show the banner when nothing needs action', () => {
    const waitingOnly: PurchaseRequestListItem[] = [requests[0]];
    render(<PurchaseRequestsList {...baseProps()} requests={waitingOnly} />);
    expect(screen.queryByText(/need.*your attention/i)).not.toBeInTheDocument();
  });

  it('filters to Needs Action / Waiting / Completed via the quick filter buttons', async () => {
    const user = userEvent.setup();
    const onBucketFilterChange = vi.fn();
    render(<PurchaseRequestsList {...baseProps()} onBucketFilterChange={onBucketFilterChange} />);

    await user.click(screen.getByRole('button', { name: /^needs action/i }));
    expect(onBucketFilterChange).toHaveBeenCalledWith('needs_action');
  });

  it('shows only requests in the selected bucket', () => {
    render(<PurchaseRequestsList {...baseProps()} bucketFilter="needs_action" />);
    expect(screen.getByText('PR-0002')).toBeInTheDocument();
    expect(screen.queryByText('PR-0001')).not.toBeInTheDocument();
  });

  it('renders the server-supplied total_estimated_cost verbatim (regression: no client-side qty math to get wrong)', () => {
    // The list endpoint never sends item-level quantity/cost - only the
    // pre-computed aggregate - so the card has no data to recompute a total
    // from and must simply display what the server sent, e.g. a multi-unit
    // line (qty 10 x $1.00 unit cost) whose correct total is $10.00.
    const multiUnit: PurchaseRequestListItem[] = [
      { ...requests[0], id: 3, requisition_number: 'PR-0003', total_estimated_cost: '10.00' },
    ];
    render(<PurchaseRequestsList {...baseProps()} requests={multiUnit} />);
    expect(screen.getByText('$10.00')).toBeInTheDocument();
  });

  it('shows correct bucket counts on the filter buttons', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    // 1 REJECTED (needs action), 1 PENDING_* (waiting), 0 PROCESSED (completed), 2 total.
    expect(screen.getByRole('button', { name: /needs action \(1\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /waiting \(1\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /completed \(0\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /all \(2\)/i })).toBeInTheDocument();
  });
});
