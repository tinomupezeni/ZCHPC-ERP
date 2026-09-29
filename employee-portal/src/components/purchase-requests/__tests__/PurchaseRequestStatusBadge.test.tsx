import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PurchaseRequestStatusBadge } from '../PurchaseRequestStatusBadge';

describe('PurchaseRequestStatusBadge', () => {
  it('renders a human-readable, action-oriented label for a pending status', () => {
    render(<PurchaseRequestStatusBadge status="PENDING_DEPARTMENT_HEAD" />);
    expect(screen.getByText('Awaiting Department Head')).toBeInTheDocument();
    expect(screen.queryByText('PENDING_DEPARTMENT_HEAD')).not.toBeInTheDocument();
  });

  it('labels DRAFT as "Not Submitted" rather than the internal term', () => {
    render(<PurchaseRequestStatusBadge status="DRAFT" />);
    expect(screen.getByText('Not Submitted')).toBeInTheDocument();
    expect(screen.queryByText('Draft')).not.toBeInTheDocument();
  });

  it('labels REJECTED as "Correction Required" rather than a bare historical term', () => {
    render(<PurchaseRequestStatusBadge status="REJECTED" />);
    expect(screen.getByText('Correction Required')).toBeInTheDocument();
  });

  it('labels PROCESSED as "Completed"', () => {
    render(<PurchaseRequestStatusBadge status="PROCESSED" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });
});
