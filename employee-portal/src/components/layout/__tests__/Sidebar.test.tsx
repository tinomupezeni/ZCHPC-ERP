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

/**
 * F20 follow-up: Department Head Review / Accounts Verification visibility
 * is driven entirely by usePurchaseRequestReviewerAccess (the real backend
 * queue-endpoint outcome), independent of roleGroup - not by roleGroup, and
 * not by useRole() at all. See the hook's own docstring for why: the seeded
 * PR_TEST_* accounts all resolve to the 'staff' roleGroup regardless of
 * which one actually holds reviewer authority.
 */
let mockCanReviewAsDepartmentHead: boolean | null = false;
let mockCanVerifyAsAccounts: boolean | null = false;
vi.mock('@/hooks/usePurchaseRequestReviewerAccess', () => ({
  usePurchaseRequestReviewerAccess: () => ({
    canReviewAsDepartmentHead: mockCanReviewAsDepartmentHead,
    canVerifyAsAccounts: mockCanVerifyAsAccounts,
  }),
}));

function renderSidebar() {
  return render(
    <MemoryRouter>
      <Sidebar isOpen onClose={vi.fn()} />
    </MemoryRouter>
  );
}

describe('Sidebar - F20 follow-up: permission-aware Purchase Request review navigation', () => {
  it('shows "Department Head Review" only when the reviewer-access check says so, regardless of role group', () => {
    mockRoleGroup = 'staff';
    mockUseActionCount.mockReturnValue(0);
    mockCanReviewAsDepartmentHead = true;
    mockCanVerifyAsAccounts = false;
    renderSidebar();

    expect(
      screen.getByRole('link', { name: /department head review/i })
    ).toHaveAttribute('href', '/portal/purchase-requests/review');
  });

  it('does not show "Department Head Review" for an ordinary requester (no reviewer access), and leaves requester navigation intact', () => {
    mockRoleGroup = 'staff';
    mockUseActionCount.mockReturnValue(0);
    mockCanReviewAsDepartmentHead = false;
    mockCanVerifyAsAccounts = false;
    renderSidebar();

    expect(
      screen.queryByRole('link', { name: /department head review/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: /accounts verification/i })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: /^purchase requests raise a requisition$/i })
    ).toHaveAttribute('href', '/portal/purchase-requests');
    expect(screen.getByRole('link', { name: /leave/i })).toHaveAttribute(
      'href',
      '/portal/leave'
    );
  });

  it('does not show either reviewer link while the access check is still in flight (null)', () => {
    mockRoleGroup = 'staff';
    mockUseActionCount.mockReturnValue(0);
    mockCanReviewAsDepartmentHead = null;
    mockCanVerifyAsAccounts = null;
    renderSidebar();

    expect(
      screen.queryByRole('link', { name: /department head review/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: /accounts verification/i })
    ).not.toBeInTheDocument();
  });

  it('shows "Accounts Verification" only when the reviewer-access check says so, regardless of role group', () => {
    mockRoleGroup = 'staff';
    mockUseActionCount.mockReturnValue(0);
    mockCanReviewAsDepartmentHead = false;
    mockCanVerifyAsAccounts = true;
    renderSidebar();

    expect(
      screen.getByRole('link', { name: /accounts verification/i })
    ).toHaveAttribute('href', '/portal/purchase-requests/accounts');
  });

  it('shows both reviewer links together when both checks pass', () => {
    mockRoleGroup = 'staff';
    mockUseActionCount.mockReturnValue(0);
    mockCanReviewAsDepartmentHead = true;
    mockCanVerifyAsAccounts = true;
    renderSidebar();

    expect(
      screen.getByRole('link', { name: /department head review/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: /accounts verification/i })
    ).toBeInTheDocument();
  });

  it('does not confuse the existing "Accounts" ledger link with the new "Accounts Verification" link', () => {
    mockRoleGroup = 'accountant';
    mockUseActionCount.mockReturnValue(0);
    mockCanReviewAsDepartmentHead = false;
    mockCanVerifyAsAccounts = true;
    renderSidebar();

    expect(screen.getByRole('link', { name: /^accounts ledgers & accounts$/i })).toHaveAttribute(
      'href',
      '/portal/accounts'
    );
    expect(
      screen.getByRole('link', { name: /accounts verification/i })
    ).toHaveAttribute('href', '/portal/purchase-requests/accounts');
  });

  it('leaves the accountant role group navigation unaffected when reviewer access is false', () => {
    mockRoleGroup = 'accountant';
    mockUseActionCount.mockReturnValue(0);
    mockCanReviewAsDepartmentHead = false;
    mockCanVerifyAsAccounts = false;
    renderSidebar();

    expect(
      screen.queryByRole('link', { name: /accounts verification/i })
    ).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^accounts ledgers & accounts$/i })).toHaveAttribute(
      'href',
      '/portal/accounts'
    );
  });
});

describe('Sidebar - Purchase Requests action badge', () => {
  it('shows no badge when there is nothing needing action', () => {
    mockRoleGroup = 'staff';
    mockCanReviewAsDepartmentHead = false;
    mockCanVerifyAsAccounts = false;
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
