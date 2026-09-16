import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RequesterInfoCard } from '../RequesterInfoCard';
import type { Employee } from '@/types/auth.types';

const employee: Employee = {
  id: 1,
  employee_id: 'EMP001',
  first_name: 'Richard',
  surname: 'Matsika',
  full_name: 'Richard Matsika',
  email: 'richard@zchpc.test',
  phone: '+263771234567',
  gender: 'M',
  date_of_birth: null,
  date_joined: '2024-01-01',
  department_name: 'IT Department',
  position_title: 'Systems Administrator',
  role_name: 'REGULAR_STAFF',
  role_display_name: 'Regular Staff',
  employee_type: 'FULL_TIME',
  is_active: true,
  leave_days_entitled: 21,
};

describe('RequesterInfoCard', () => {
  it('presents the authenticated employee\'s own details, read-only', () => {
    render(<RequesterInfoCard employee={employee} />);

    expect(screen.getByText('Richard Matsika')).toBeInTheDocument();
    expect(screen.getByText('EMP001')).toBeInTheDocument();
    expect(screen.getByText('Systems Administrator')).toBeInTheDocument();
    expect(screen.getByText('+263771234567')).toBeInTheDocument();
    expect(screen.getByText('IT Department')).toBeInTheDocument();
  });

  it('falls back to email when no phone is on file', () => {
    render(<RequesterInfoCard employee={{ ...employee, phone: '' }} />);
    expect(screen.getByText('richard@zchpc.test')).toBeInTheDocument();
  });

  it('renders no editable inputs - requester identity cannot be changed by the employee', () => {
    render(<RequesterInfoCard employee={employee} />);
    expect(screen.queryAllByRole('textbox')).toHaveLength(0);
    expect(screen.queryAllByRole('combobox')).toHaveLength(0);
  });

  it('contains no request-on-behalf-of affordance', () => {
    render(<RequesterInfoCard employee={employee} />);
    expect(screen.queryByText(/on behalf/i)).not.toBeInTheDocument();
  });
});
