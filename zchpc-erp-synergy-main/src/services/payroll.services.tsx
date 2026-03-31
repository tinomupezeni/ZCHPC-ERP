import apiClient  from "./apiClient";

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