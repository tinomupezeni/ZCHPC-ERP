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
    statusFilter: 'all' as const,
    onStatusFilterChange: vi.fn(),
  };
}

describe('PurchaseRequestsList', () => {
  it('shows a loading state', () => {
    render(<PurchaseRequestsList {...baseProps()} isLoading requests={[]} />);
    expect(screen.getByText('My Purchase Requests')).toBeInTheDocument();
    expect(screen.queryByText('PR-0001')).not.toBeInTheDocument();
  });

  it('shows an empty state when there are no requests', () => {
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

  it('renders human-readable statuses, not raw enum strings', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    expect(screen.getByText('Pending Department Head')).toBeInTheDocument();
    expect(screen.getByText('Rejected')).toBeInTheDocument();
    expect(screen.queryByText('PENDING_DEPARTMENT_HEAD')).not.toBeInTheDocument();
  });

  it('shows the requisition number, date and total on each card', () => {
    render(<PurchaseRequestsList {...baseProps()} />);
    expect(screen.getByText('PR-0001')).toBeInTheDocument();
    expect(screen.getByText('$800.00')).toBeInTheDocument();
    expect(screen.getByText('PR-0002')).toBeInTheDocument();
    expect(screen.getByText('$150.00')).toBeInTheDocument();
  });

  it('opens the request detail when a card is clicked', async () => {
    const user = userEvent.setup();
    const onView = vi.fn();
    render(<PurchaseRequestsList {...baseProps()} onView={onView} />);

    await user.click(screen.getByText('PR-0001'));
    expect(onView).toHaveBeenCalledWith(1);
  });
});
