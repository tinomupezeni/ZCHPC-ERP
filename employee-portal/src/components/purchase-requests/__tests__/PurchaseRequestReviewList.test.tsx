import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PurchaseRequestReviewList } from '../PurchaseRequestReviewList';
import type { PurchaseRequestListItem } from '@/types/purchase-request.types';

function pendingRequest(
  overrides: Partial<PurchaseRequestListItem> = {}
): PurchaseRequestListItem {
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

describe('PurchaseRequestReviewList - loading', () => {
  it('shows a loading skeleton instead of the queue', () => {
    render(
      <PurchaseRequestReviewList
        requests={[]}
        isLoading
        error={null}
        onRetry={vi.fn()}
        onView={vi.fn()}
      />
    );

    expect(screen.getByText('Pending Requests')).toBeInTheDocument();
    expect(screen.queryByText('No requests waiting for your review.')).not.toBeInTheDocument();
  });
});

describe('PurchaseRequestReviewList - successful queue rendering', () => {
  it('renders requisition number, requester, department, total cost and status for each row', () => {
    render(
      <PurchaseRequestReviewList
        requests={[pendingRequest()]}
        isLoading={false}
        error={null}
        onRetry={vi.fn()}
        onView={vi.fn()}
      />
    );

    expect(screen.getByText('PR-0042')).toBeInTheDocument();
    expect(screen.getByText(/Jane Moyo/)).toBeInTheDocument();
    expect(screen.getByText(/IT Department/)).toBeInTheDocument();
    expect(screen.getByText('$1,200.00')).toBeInTheDocument();
    expect(screen.getByText('Awaiting Department Head')).toBeInTheDocument();
  });

  it('calls onView with the request id when a row is clicked', async () => {
    const user = userEvent.setup();
    const onView = vi.fn();
    render(
      <PurchaseRequestReviewList
        requests={[pendingRequest({ id: 99 })]}
        isLoading={false}
        error={null}
        onRetry={vi.fn()}
        onView={onView}
      />
    );

    await user.click(screen.getByText('PR-0042'));

    expect(onView).toHaveBeenCalledWith(99);
  });
});

describe('PurchaseRequestReviewList - empty queue', () => {
  it('shows the empty-queue message when there are no pending requests', () => {
    render(
      <PurchaseRequestReviewList
        requests={[]}
        isLoading={false}
        error={null}
        onRetry={vi.fn()}
        onView={vi.fn()}
      />
    );

    expect(screen.getByText('No requests waiting for your review.')).toBeInTheDocument();
  });
});

describe('PurchaseRequestReviewList - unauthorized (403)', () => {
  it('shows a distinct access-denied state, never the empty-queue message', () => {
    render(
      <PurchaseRequestReviewList
        requests={[]}
        isLoading={false}
        error={{ kind: 'unauthorized', message: 'You do not have access to this queue.' }}
        onRetry={vi.fn()}
        onView={vi.fn()}
      />
    );

    expect(screen.getByText("You don't have access to this queue")).toBeInTheDocument();
    expect(screen.getByText('You do not have access to this queue.')).toBeInTheDocument();
    expect(screen.queryByText('No requests waiting for your review.')).not.toBeInTheDocument();
    // No retry affordance for an authorization failure - retrying changes nothing.
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });
});

describe('PurchaseRequestReviewList - generic API failure', () => {
  it('shows the error message and a retry button', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(
      <PurchaseRequestReviewList
        requests={[]}
        isLoading={false}
        error={{ kind: 'generic', message: 'Failed to load requests awaiting your review' }}
        onRetry={onRetry}
        onView={vi.fn()}
      />
    );

    expect(
      screen.getByText('Failed to load requests awaiting your review')
    ).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
