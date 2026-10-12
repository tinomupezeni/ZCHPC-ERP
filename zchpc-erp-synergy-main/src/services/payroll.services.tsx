import apiClient  from "./apiClient";

// --- Types ---

// One row of GET /payroll/payslips/?period= (PayslipListSerializer). Amounts
// arrive as decimal strings; the list has gross, not base salary (PY-6).
export interface PayrollRecord {
  id: number;
  employee_id: string;
  employee_name: string; // full name
  department: string;
  period: string; // "YYYY-MM"
  gross_usd: string;
  gross_zig: string;
  net_salary_usd: string;
  net_salary_zig: string;
  status: "Draft" | "Pending" | "Processed" | "Paid" | "Failed";
}

// GET /payroll/payslips/<id>/ (PayslipDetailView): the full breakdown.
export interface PayslipDetail {
  id: number;
  employee_id: string;
  employee_name: string;
  department: string;
  period: string;
  base_salary_usd: string;
  base_salary_zig: string;
  total_allowances_usd: string;
  total_allowances_zig: string;
  gross_usd: string;
  gross_zig: string;
  paye_usd: string;
  paye_zig: string;
  aids_levy_usd: string;
  aids_levy_zig: string;
  nssa_employee_usd: string;
  nssa_employee_zig: string;
  other_deductions_usd: string;
  other_deductions_zig: string;
  net_salary_usd: string;
  net_salary_zig: string;
  exchange_rate: string;
  status: PayrollRecord["status"];
}

export interface ProcessPayrollParams {
  month: string; // Format: "YYYY-MM"
}

// --- API Functions ---

/**
 * Fetch payslips for a specific month/period
 */
export const getPayslips = async (period: string) => {
  // Backend endpoint: /api/v2/payroll/payslips/?period=YYYY-MM
  const response = await apiClient.get<PayrollRecord[]>(`/payroll/payslips/`, {
    params: { period }
  });
  return response.data;
};

/**
 * Trigger the payroll processing engine for a specific month
 */
export const processPayroll = async (data: ProcessPayrollParams) => {
  const response = await apiClient.post("/payroll/payslips/", data);
  return response.data;
};

export const getPayslipDetail = async (id: number) => {
  const response = await apiClient.get<PayslipDetail>(`/payroll/payslips/${id}/`);
  return response.data;
};

/** The server's reason for a refused payroll action, if it gave one. */
export const payrollErrorMessage = (error: any, fallback: string): string =>
  error?.response?.data?.error || error?.response?.data?.detail || fallback;

/**
 * Approve a specific payslip
 */
export const approvePayslip = async (id: number) => {
  const response = await apiClient.post(`/payroll/payslips/${id}/approve/`);
  return response.data;
};

/**
 * Delete a payslip (e.g. rollback for one person)
 */
export const deletePayslip = async (id: number) => {
  await apiClient.delete(`/payroll/payslips/${id}/`);
};

/**
 * Fetch summary statistics for the dashboard cards
 */
export const getPayrollSummary = async (period: string) => {
  const response = await apiClient.get(`/payroll/summary/`, {
    params: { period }
  });
  return response.data;
}; 