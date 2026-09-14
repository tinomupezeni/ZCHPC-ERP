import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PurchaseRequestStatusBadge } from '../PurchaseRequestStatusBadge';

describe('PurchaseRequestStatusBadge', () => {
  it('renders a human-readable label for a pending status', () => {
    render(<PurchaseRequestStatusBadge status="PENDING_DEPARTMENT_HEAD" />);
    expect(screen.getByText('Pending Department Head')).toBeInTheDocument();
  });
});
