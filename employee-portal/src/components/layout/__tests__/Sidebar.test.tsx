import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../Sidebar';

let mockRoleGroup = 'staff';
vi.mock('@/hooks/useRole', () => ({
  useRole: () => ({ roleGroup: mockRoleGroup }),
}));

const mockUseActionCount = vi.fn();
vi.mock('@/hooks/usePurchaseRequestActionCount', () => ({
  usePurchaseRequestActionCount: () => mockUseActionCount(),
}));

function renderSidebar() {
  return render(
    <MemoryRouter>
      <Sidebar isOpen onClose={vi.fn()} />
    </MemoryRouter>
  );
}

describe('Sidebar - F17 Department Head review navigation', () => {
  it('shows a "Review Purchase Requests" link for the manager role group', () => {
    mockRoleGroup = 'manager';
    mockUseActionCount.mockReturnValue(0);
    renderSidebar();

    expect(
      screen.getByRole('link', { name: /review purchase requests/i })
    ).toHaveAttribute('href', '/portal/purchase-requests/review');
  });

  it('does not show the review link for the staff role group, and leaves the existing requester navigation intact', () => {
    mockRoleGroup = 'staff';
    mockUseActionCount.mockReturnValue(0);
    renderSidebar();

    expect(
      screen.queryByRole('link', { name: /review purchase requests/i })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: /^purchase requests raise a requisition$/i })
    ).toHaveAttribute('href', '/portal/purchase-requests');
    expect(screen.getByRole('link', { name: /leave/i })).toHaveAttribute(
      'href',
      '/portal/leave'
    );
  });
});

describe('Sidebar - F18 Accounts verification navigation', () => {
  it('shows an "Accounts Verification" link for the accountant role group', () => {
    mockRoleGroup = 'accountant';
    mockUseActionCount.mockReturnValue(0);
    renderSidebar();

    expect(
      screen.getByRole('link', { name: /accounts verification/i })
    ).toHaveAttribute('href', '/portal/purchase-requests/accounts');
  });

  it('does not show the accounts verification link for the staff role group, and leaves the existing requester navigation intact', () => {
    mockRoleGroup = 'staff';
    mockUseActionCount.mockReturnValue(0);
    renderSidebar();

    expect(
      screen.queryByRole('link', { name: /accounts verification/i })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: /^purchase requests raise a requisition$/i })
    ).toHaveAttribute('href', '/portal/purchase-requests');
  });

  it('does not confuse the existing "Accounts" ledger link with the new "Accounts Verification" link', () => {
    mockRoleGroup = 'accountant';
    mockUseActionCount.mockReturnValue(0);
    renderSidebar();

    expect(screen.getByRole('link', { name: /^accounts ledgers & accounts$/i })).toHaveAttribute(
      'href',
      '/portal/accounts'
    );
    expect(
      screen.getByRole('link', { name: /accounts verification/i })
    ).toHaveAttribute('href', '/portal/purchase-requests/accounts');
  });
});

describe('Sidebar - Purchase Requests action badge', () => {
  it('shows no badge when there is nothing needing action', () => {
    mockRoleGroup = 'staff';
    mockUseActionCount.mockReturnValue(0);
    renderSidebar();

    const link = screen.getByRole('link', { name: /purchase requests/i });
    expect(link).not.toHaveTextContent(/\d/);
  });

  it('shows a subtle count badge when requests need action', () => {
    mockUseActionCount.mockReturnValue(2);
    renderSidebar();

    const link = screen.getByRole('link', { name: /purchase requests/i });
    expect(link).toHaveTextContent('2');
  });

  it('does not add a badge to any other nav item', () => {
    mockUseActionCount.mockReturnValue(3);
    renderSidebar();

    const leaveLink = screen.getByRole('link', { name: /leave/i });
    expect(leaveLink).not.toHaveTextContent('3');
  });
});
