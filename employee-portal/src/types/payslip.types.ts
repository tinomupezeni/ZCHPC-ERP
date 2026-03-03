export type PayslipStatus = 'Draft' | 'Pending' | 'Processed' | 'Failed' | 'Paid';

export interface PayslipListItem {
  id: number;
  period: string;
  period_display: string;
  month: number;
  year: number;
  status: PayslipStatus;
  base_salary_usd: number;
  net_salary_usd: number;
  base_salary_zig: number;
  net_salary_zig: number;
  exchange_rate: number;
}

export interface PayslipsResponse {
  payslips: PayslipListItem[];
  available_years: number[];
  current_year: number;
}

export interface CurrencyAmount {
  usd: number;
  zig: number;
}

export interface PayslipEarnings {
  base_salary: CurrencyAmount;
  allowances: CurrencyAmount;
  gross: CurrencyAmount;
}

export interface PayslipDeductions {
  paye: CurrencyAmount;
  aids_levy: CurrencyAmount;
  nssa_employee: CurrencyAmount;
  other_deductions: CurrencyAmount;
  total: CurrencyAmount;
}

export interface PayslipSummary {
  gross_salary: CurrencyAmount;
  total_deductions: CurrencyAmount;
  net_salary: CurrencyAmount;
}

export interface PayslipDetail {
  id: number;
  period: string;
  period_display: string;
  month: number;
  year: number;
  status: PayslipStatus;
  employee_name: string;
  employee_id: string;
  department: string;
  position: string;
  exchange_rate: number;
  earnings: PayslipEarnings;
  deductions: PayslipDeductions;
  summary: PayslipSummary;
  notes: string;
  created_at: string;
}

export interface PayslipYearSummary {
  year: number;
  total_gross_usd: number;
  total_gross_zig: number;
  total_deductions_usd: number;
  total_deductions_zig: number;
  total_net_usd: number;
  total_net_zig: number;
  payslip_count: number;
}
