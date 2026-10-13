import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import type { InternalAxiosRequestConfig } from 'axios';
import api from '../api';
import { authService } from '../auth.service';

/**
 * Found 2026-10-13: the portal profile (EmployeeProfileSerializer, used by
 * login and /portal/auth/me/) sends first_name and surname but no full_name,
 * so the header's user menu and the purchase request's "Requested By" were
 * blank. The payload below is exactly the serializer's fields.
 */
const apiProfile = {
  id: 8,
  employee_id: 'EMP0008',
  first_name: 'Tinashe',
  surname: 'Dube',
  email: 'tinashe.dube@zchpc.ac.zw',
  phone: null,
  department_id: 1,
  department_name: 'IT',
  position_id: 3,
  position_name: 'Systems Engineer',
};

const ok = (config: InternalAxiosRequestConfig, data: unknown) => ({
  data, status: 200, statusText: 'OK', headers: {}, config,
});

let originalAdapter: typeof api.defaults.adapter;
beforeEach(() => { originalAdapter = api.defaults.adapter; localStorage.clear(); });
afterEach(() => { api.defaults.adapter = originalAdapter; });

describe('portal profile full name', () => {
  it('builds full_name for /portal/auth/me/', async () => {
    api.defaults.adapter = async (config) => ok(config, apiProfile);
    const employee = await authService.getCurrentEmployee();
    expect(employee.full_name).toBe('Tinashe Dube');
  });

  it('builds full_name for the login response', async () => {
    api.defaults.adapter = async (config) =>
      ok(config, { access: 'a', refresh: 'r', employee: apiProfile });
    const response = await authService.login({ employee_id: 'EMP0008', password: 'x' } as never);
    expect(response.employee.full_name).toBe('Tinashe Dube');
  });
});
