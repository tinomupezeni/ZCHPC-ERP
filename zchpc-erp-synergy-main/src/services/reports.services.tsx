import apiClient from "./apiClient";

export interface ReportData {
  id: number;
  employee_name?: string;
  employeeName?: string;
  [key: string]: any; // Allow dynamic fields based on report type
}

export interface ReportSummary {
  total_employees: number;
  payroll_records: number;
  total_gross_salary_usd: number;
  total_net_salary_usd: number;
  total_paye_usd: number;
  total_nssa_usd: number;
  total_allowances_usd: number;
  total_deductions_usd: number;
}

// Report type to endpoint mapping
const REPORT_ENDPOINTS: Record<string, string> = {
  // Core Payroll Reports
  basicSalary: "/reports/basic-salary/",
  paye: "/reports/paye/",
  nssa: "/reports/nssa/",

  // Benefits Reports
  allowances: "/reports/allowances/",

  // Deductions Reports
  deductions: "/reports/deductions/",

  // HR Analytics Reports
  leaveBalance: "/reports/leave-balances/",
  training: "/reports/training/",
  employees: "/reports/employees/",
};

/**
 * Central function to fetch data based on the selected report type.
 */
export const fetchReportData = async (
  reportType: string,
  filters?: { period?: string; department?: string; status?: string; year?: string }
): Promise<ReportData[]> => {
  const endpoint = REPORT_ENDPOINTS[reportType];

  if (!endpoint) {
    console.warn(`Report type "${reportType}" not yet implemented.`);
    return [];
  }

  try {
    // Build query params from filters
    const params = new URLSearchParams();
    if (filters?.period) params.append("period", filters.period);
    if (filters?.department) params.append("department", filters.department);
    if (filters?.status) params.append("status", filters.status);
    if (filters?.year) params.append("year", filters.year);

    const queryString = params.toString();
    const url = `/hr${endpoint}${queryString ? `?${queryString}` : ""}`;

    const response = await apiClient.get<ReportData[]>(url);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch ${reportType} report:`, error);
    throw error;
  }
};

/**
 * Fetch summary statistics for the reports dashboard
 */
export const fetchReportSummary = async (period?: string): Promise<ReportSummary> => {
  try {
    const url = period
      ? `/hr/reports/summary/?period=${period}`
      : "/hr/reports/summary/";
    const response = await apiClient.get<ReportSummary>(url);
    return response.data;
  } catch (error) {
    console.error("Failed to fetch report summary:", error);
    throw error;
  }
};

/**
 * Get available payroll periods for filtering
 */
export const fetchPayrollPeriods = async (): Promise<{ period: string; label: string }[]> => {
  try {
    // This would ideally come from a dedicated endpoint
    // For now, we'll generate recent months
    const periods: { period: string; label: string }[] = [];
    const now = new Date();

    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const period = date.toISOString().split("T")[0];
      const label = date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
      periods.push({ period, label });
    }

    return periods;
  } catch (error) {
    console.error("Failed to fetch payroll periods:", error);
    return [];
  }
};

/**
 * Export report data to CSV
 */
export const exportReportToCSV = (data: ReportData[], filename: string): void => {
  if (!data || data.length === 0) {
    console.warn("No data to export");
    return;
  }

  // Get headers from first item
  const headers = Object.keys(data[0]).filter((key) => key !== "id");

  // Create CSV content
  const csvContent = [
    headers.join(","),
    ...data.map((row) =>
      headers
        .map((header) => {
          const value = row[header];
          // Escape commas and quotes
          if (typeof value === "string" && (value.includes(",") || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value ?? "";
        })
        .join(",")
    ),
  ].join("\n");

  // Create and download file
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
