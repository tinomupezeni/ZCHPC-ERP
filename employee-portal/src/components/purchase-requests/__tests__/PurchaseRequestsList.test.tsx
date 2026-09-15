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

  it('does not render any editing/resubmission CTA for a rejected request', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    for (const name of [/continue/i, /edit/i, /\bcorrect\b/i, /resubmit/i]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument();
    }
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

  it('shows correct bucket counts on the filter buttons', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    // 1 REJECTED (needs action), 1 PENDING_* (waiting), 0 PROCESSED (completed), 2 total.
    expect(screen.getByRole('button', { name: /needs action \(1\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /waiting \(1\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /completed \(0\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /all \(2\)/i })).toBeInTheDocument();
  });
});
