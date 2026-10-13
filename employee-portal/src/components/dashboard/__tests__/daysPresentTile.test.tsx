import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { Employee } from '@/types/auth.types';
import type { DashboardSummary } from '@/types/dashboard.types';

/**
 * Found 2026-10-13: every role dashboard's "Days Present" read
 * attendance_this_month, which /portal/dashboard/ never sends (it sends
 * monthly_attendance_count), so the tile always showed 0. The payload below
 * uses DashboardSerializer's field names.
 */
const employee = { id: 8, employee_id: 'EMP0008', full_name: 'Tinashe Dube' } as Employee;

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ employee, logout: vi.fn() }),
}));

const { StaffDashboard } = await import('../role/StaffDashboard');

const apiPayload: DashboardSummary = {
  employee_id: 'EMP0008',
  employee_name: 'Tinashe Dube',
  department_name: 'IT',
  position_name: 'Systems Engineer',
  leave_balances: [],
  monthly_attendance_count: 7,
  recent_attendance: [],
  pending_leave_requests: 0,
  leave_requests_to_review: 0,
  pending_expense_claims: 0,
  open_tickets: 0,
  unread_notifications: 0,
  upcoming_events: [],
};

describe('Days Present tile', () => {
  it('shows the monthly attendance count the API sends', () => {
    render(
      <MemoryRouter>
        <StaffDashboard data={apiPayload} />
      </MemoryRouter>
    );

    const tile = screen.getByText('Days Present').closest('div')!.parentElement!;
    expect(tile.textContent).toContain('7');
  });
});
