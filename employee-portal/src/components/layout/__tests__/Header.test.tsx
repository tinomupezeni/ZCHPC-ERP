import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { Employee } from '@/types/auth.types';

/**
 * F27 follow-up: the notification bell must render for every authenticated
 * Employee Portal user, regardless of role - Header itself never branches
 * on role/permissions around <NotificationBell />, so these tests mount it
 * with several distinct employee shapes (the roles the manual UI testing
 * report named: employee, accountant, department head, reviewer) and check
 * the bell is present every time. useNotifications is stubbed to an idle,
 * error-free state so this stays focused on rendering, not fetch behaviour
 * (already covered by NotificationBell.test.tsx).
 */
vi.mock('@/hooks/useNotifications', () => ({
  useNotifications: () => ({
    unreadCount: 0,
    notifications: [],
    isLoading: false,
    error: null,
    loadNotifications: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
  }),
}));

let mockEmployee: Employee | null = null;
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ employee: mockEmployee, logout: vi.fn() }),
}));

const { Header } = await import('../Header');

function baseEmployee(overrides: Partial<Employee> = {}): Employee {
  return {
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
    ...overrides,
  };
}

function renderHeader() {
  return render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>
  );
}

describe('Header - notification bell renders for every authenticated role (F27 follow-up)', () => {
  it.each([
    ['ordinary employee', { role_name: 'REGULAR_STAFF', role_display_name: 'Regular Staff' }],
    ['accountant', { role_name: 'ACCOUNTANT', role_display_name: 'Accountant' }],
    [
      'department head',
      { role_name: 'DEPARTMENT_MANAGER', role_display_name: 'Department Manager' },
    ],
    ['GM reviewer', { role_name: 'GENERAL_MANAGER', role_display_name: 'General Manager' }],
    ['director reviewer', { role_name: 'DIRECTOR', role_display_name: 'Director' }],
    [
      'procurement reviewer',
      { role_name: 'PROCUREMENT_OFFICER', role_display_name: 'Procurement Officer' },
    ],
  ])('renders the bell for %s', (_label, overrides) => {
    mockEmployee = baseEmployee(overrides);

    renderHeader();

    expect(screen.getByRole('button', { name: 'Notifications' })).toBeInTheDocument();
  });

  it('renders the bell even when no employee profile has loaded yet', () => {
    mockEmployee = null;

    renderHeader();

    expect(screen.getByRole('button', { name: 'Notifications' })).toBeInTheDocument();
  });
});
