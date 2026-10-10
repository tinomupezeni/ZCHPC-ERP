import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { PayslipDetail } from '@/types/payslip.types';

/**
 * PY-3: the printable payslip replaces the download. It sits outside
 * MainLayout, so it applies the evaluation's availability list itself.
 */
let payslipsAvailable = false;
vi.mock('@/components/layout/navAvailability', () => ({
  availabilityFor: (path: string) =>
    !payslipsAvailable && path.startsWith('/portal/payslips') ? 'not-available' : undefined,
}));

const getPayslip = vi.fn();
vi.mock('@/services/payslip.service', () => ({
  payslipService: { getPayslip: (id: number) => getPayslip(id) },
}));

const { PayslipPrintPage } = await import('../PayslipPrintPage');

const amount = (usd: number, zig: number) => ({ usd, zig });

const payslip: PayslipDetail = {
  id: 7,
  period: '2026-09',
  period_display: 'September 2026',
  month: 9,
  year: 2026,
  status: 'Processed',
  employee_name: 'Dina Person',
  employee_id: 'EMP0007',
  department: 'Finance',
  position: 'Analyst',
  exchange_rate: 26,
  earnings: {
    base_salary: amount(1000, 26000),
    allowances: amount(200, 5200),
    gross: amount(1200, 31200),
  },
  deductions: {
    paye: amount(120, 0),
    aids_levy: amount(3.6, 0),
    nssa_employee: amount(20, 0),
    other_deductions: amount(6.4, 0),
    total: amount(150, 0),
  },
  summary: {
    gross_salary: amount(1200, 31200),
    total_deductions: amount(150, 0),
    net_salary: amount(1050, 27300),
  },
  notes: '',
  created_at: '2026-09-30T10:00:00Z',
};

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/portal/payslips/:id/print" element={<PayslipPrintPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('PayslipPrintPage', () => {
  beforeEach(() => {
    getPayslip.mockReset();
  });

  it('is "Not available" while the evaluation lists payslips, and fetches nothing', () => {
    payslipsAvailable = false;
    renderAt('/portal/payslips/7/print');

    expect(screen.getByText('Not available in this evaluation')).toBeTruthy();
    expect(getPayslip).not.toHaveBeenCalled();
  });

  it('prints the payslip, labelled indicative', async () => {
    payslipsAvailable = true;
    getPayslip.mockResolvedValue(payslip);
    renderAt('/portal/payslips/7/print');

    expect(await screen.findByText('PAYSLIP - SEPTEMBER 2026')).toBeTruthy();
    expect(getPayslip).toHaveBeenCalledWith(7);
    expect(screen.getByText('Dina Person')).toBeTruthy();
    expect(screen.getByText('1,050.00')).toBeTruthy();
    expect(screen.getByText(/Indicative figures/)).toBeTruthy();
    expect(screen.getByRole('button', { name: /Print/ })).toBeTruthy();
  });

  it('says so when the payslip cannot be loaded', async () => {
    payslipsAvailable = true;
    getPayslip.mockRejectedValue(new Error('404'));
    renderAt('/portal/payslips/99/print');

    expect(await screen.findByText('Payslip not found.')).toBeTruthy();
  });
});
