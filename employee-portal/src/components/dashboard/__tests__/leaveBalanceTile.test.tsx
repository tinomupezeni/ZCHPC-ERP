import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { Employee } from '@/types/auth.types';

/**
 * While the evaluation marks the leave-balance tile not available, no role
 * dashboard shows a figure for it - not even the employee's entitlement,
 * which the tile used to show as if it were the balance.
 */
const employee = {
  id: 1,
  employee_id: 'EMP001',
  first_name: 'Test',
  surname: 'User',
  full_name: 'Test User',
  email: 'test@zchpc.test',
  phone: '+263771234567',
  gender: 'M',
  date_of_birth: null,
  date_joined: '2024-01-01',
  department_name: 'IT Department',
  position_title: 'Staff',
  role_name: 'REGULAR_STAFF',
  role_display_name: 'Regular Staff',
  employee_type: 'FULL_TIME',
  is_active: true,
  leave_days_entitled: 21,
} as Employee;

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ employee, logout: vi.fn() }),
}));

const { StaffDashboard } = await import('../role/StaffDashboard');
const { HRDashboard } = await import('../role/HRDashboard');
const { ManagerDashboard } = await import('../role/ManagerDashboard');
const { AccountantDashboard } = await import('../role/AccountantDashboard');
const { ProcurementDashboard } = await import('../role/ProcurementDashboard');
const { leaveBalanceTile } = await import('../leaveBalanceTile');

describe('leave-balance tile while not available', () => {
  it('gives no figure', () => {
    expect(leaveBalanceTile(null, employee, 'days')).toEqual({
      value: '—',
      unit: 'Not available',
    });
  });

  it.each([
    ['staff', StaffDashboard, 'Leave Balance'],
    ['hr', HRDashboard, 'Your Leave Balance'],
    ['manager', ManagerDashboard, 'My Leave Balance'],
    ['accountant', AccountantDashboard, 'My Leave Balance'],
    ['procurement', ProcurementDashboard, 'My Leave Balance'],
  ])('%s dashboard marks the tile "Not available"', (_role, Dashboard, label) => {
    render(
      <MemoryRouter>
        <Dashboard data={null} />
      </MemoryRouter>
    );

    // The smallest element holding both the label and "Not available": the tile.
    let tile: HTMLElement = screen.getByText(label);
    while (!tile.textContent?.includes('Not available') && tile.parentElement) {
      tile = tile.parentElement;
    }
    expect(tile.textContent).toContain('Not available');
    expect(tile.textContent).not.toContain('21');
    expect(tile.textContent).toContain('—');
  });
});
