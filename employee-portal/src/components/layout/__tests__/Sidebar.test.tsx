import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../Sidebar';

vi.mock('@/hooks/useRole', () => ({
  useRole: () => ({ roleGroup: 'staff' }),
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

describe('Sidebar - Purchase Requests action badge', () => {
  it('shows no badge when there is nothing needing action', () => {
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
