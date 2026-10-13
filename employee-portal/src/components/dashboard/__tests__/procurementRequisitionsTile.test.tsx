import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { Employee } from '@/types/auth.types';

/**
 * Hand checks 2026-10-12: the procurement dashboard's "Requisitions" tile
 * linked /portal/requisitions, which has no route, so it fell through to the
 * public /careers page. It opens the procurement processing queue.
 */
const employee = {
  id: 7,
  employee_id: 'EMP0007',
  first_name: 'Nyasha',
  surname: 'Chiweshe',
  full_name: 'Nyasha Chiweshe',
  email: 'nyasha@zchpc.test',
  department_name: 'Procurement',
  position_name: 'Procurement Officer',
  role_name: 'PROCUREMENT_OFFICER',
  role_display_name: 'Procurement Officer',
  is_active: true,
  leave_days_entitled: 21,
} as Employee;

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ employee, logout: vi.fn() }),
}));

const { ProcurementDashboard } = await import('../role/ProcurementDashboard');

describe('procurement dashboard Requisitions tile', () => {
  it('opens the procurement processing queue, not /careers', () => {
    render(
      <MemoryRouter>
        <ProcurementDashboard data={null} />
      </MemoryRouter>
    );

    const tile = screen.getByRole('link', { name: /requisitions/i });
    expect(tile.getAttribute('href')).toBe('/portal/purchase-requests/procurement');
    const hrefs = screen.getAllByRole('link').map((link) => link.getAttribute('href'));
    expect(hrefs).not.toContain('/portal/requisitions');
  });
});
