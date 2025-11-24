import { apiClient } from "./apiClient";

// --- Types ---

export interface PayrollRecord {
  id: number;
  employee_id: string;
  employee_name: string;
  employee_surname: string;
  employee_department: string;
  period: string; // "YYYY-MM"
  
  // Financials
  base_salary_usd: number;
  base_salary_zig: number;
  net_salary_usd: number;
  net_salary_zig: number;
  
  // Status
  status: "Draft" | "Pending" | "Processed" | "Paid" | "Failed";
}

export interface ProcessPayrollParams {
  month: string; // Format: "YYYY-MM"
}

// --- API Functions ---

/**
 * Fetch payslips for a specific month/period
 */
export const getPayslips = async (period: string) => {
  // Expects backend to handle /api/payrolls/?period=2025-11
  const response = await apiClient.get<PayrollRecord[]>(`/payroll/payrolls/`, {
    params: { period }
  });
  return response.data;
};

/**
 * Trigger the payroll processing engine for a specific month
 */
export const processPayroll = async (data: ProcessPayrollParams) => {
  const response = await apiClient.post("/payroll/payrolls/process/", data);
  return response.data;
};

/**
 * Approve a specific payslip
 */
export const approvePayslip = async (id: number) => {
  const response = await apiClient.post(`/payroll/payrolls/${id}/approve/`);
  return response.data;
};

/**
 * Delete a payslip (e.g. rollback for one person)
 */
export const deletePayslip = async (id: number) => {
  await apiClient.delete(`/payroll/payrolls/${id}/`);
};

/**
 * Fetch summary statistics for the dashboard cards
 */
export const getPayrollSummary = async (period: string) => {
  const response = await apiClient.get(`/payroll/payrolls/summary/`, {
    params: { period }
  });
  return response.data;
};