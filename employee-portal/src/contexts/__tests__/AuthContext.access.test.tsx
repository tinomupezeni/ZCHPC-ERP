import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AxiosError, AxiosHeaders } from 'axios';
import type { Employee, MeAccess } from '@/types/auth.types';

/**
 * The portal's role comes from GET /auth/users/me/access/ (INT-01 §2): the
 * portal's own profile carries no role_name, so before this every login was
 * "staff". A login still holding a temporary password gets 403
 * PASSWORD_CHANGE_REQUIRED there (REM-07): it must be sent to change the
 * password, never shown an empty menu or logged out.
 */
const getCurrentEmployee = vi.fn();
const getMyAccess = vi.fn();

vi.mock('@/services/auth.service', () => ({
  authService: {
    getCurrentEmployee: () => getCurrentEmployee(),
    getMyAccess: () => getMyAccess(),
    login: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    changePassword: vi.fn(),
  },
}));

vi.mock('@/services/api', () => ({
  getAccessToken: () => 'access',
  getRefreshToken: () => 'refresh',
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
}));

const { AuthProvider, useAuth } = await import('../AuthContext');
const { useRole } = await import('@/hooks/useRole');

const employee = {
  id: 3,
  employee_id: 'EMP0003',
  first_name: 'Hana',
  surname: 'Head',
  full_name: 'Hana Head',
  email: 'hana@zchpc.test',
  role_name: null,
  role_display_name: null,
  must_change_password: false,
} as unknown as Employee;

function access(role: string): MeAccess {
  return {
    role,
    permissions: [],
    is_department_head: false,
    headed_department_ids: [],
    active_modules: [],
  };
}

function passwordChangeRequired() {
  return new AxiosError('Forbidden', '403', undefined, undefined, {
    status: 403,
    statusText: 'Forbidden',
    headers: {},
    config: { headers: new AxiosHeaders() },
    data: { code: 'PASSWORD_CHANGE_REQUIRED' },
  });
}

function Probe() {
  const { isAuthenticated, isLoading, employee: current } = useAuth();
  const { roleGroup } = useRole();
  if (isLoading) return <p>loading</p>;
  return (
    <p data-testid="state">
      {`auth=${isAuthenticated} group=${roleGroup} mustChange=${!!current?.must_change_password}`}
    </p>
  );
}

async function renderedState() {
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
  await waitFor(() => expect(screen.getByTestId('state')).toBeTruthy());
  return screen.getByTestId('state').textContent;
}

describe('portal role from /me/access/', () => {
  beforeEach(() => {
    getCurrentEmployee.mockReset();
    getMyAccess.mockReset();
  });

  it.each([
    ['DEPARTMENT_MANAGER', 'manager'],
    ['HUMAN_RESOURCES', 'hr'],
    ['ADMIN', 'admin'],
    ['REGULAR_STAFF', 'staff'],
  ])('a %s login gets the %s role group', async (role, group) => {
    getCurrentEmployee.mockResolvedValue(employee);
    getMyAccess.mockResolvedValue(access(role));

    expect(await renderedState()).toBe(`auth=true group=${group} mustChange=false`);
  });

  it('a temporary password (403 PASSWORD_CHANGE_REQUIRED) means change it, not logout', async () => {
    getCurrentEmployee.mockResolvedValue(employee);
    getMyAccess.mockRejectedValue(passwordChangeRequired());

    expect(await renderedState()).toBe('auth=true group=staff mustChange=true');
  });

  it('is not asked while the profile already says a temporary password is held', async () => {
    getCurrentEmployee.mockResolvedValue({ ...employee, must_change_password: true });

    expect(await renderedState()).toBe('auth=true group=staff mustChange=true');
    expect(getMyAccess).not.toHaveBeenCalled();
  });

  it('any other failure keeps the user signed in as staff', async () => {
    getCurrentEmployee.mockResolvedValue(employee);
    getMyAccess.mockRejectedValue(new Error('network'));

    expect(await renderedState()).toBe('auth=true group=staff mustChange=false');
  });
});
