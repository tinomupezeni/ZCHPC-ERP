import { apiClient } from "./apiClient";

export interface ReportData {
  id: number;
  employeeName: string;
  [key: string]: any; // Allow dynamic fields based on report type
}

/**
 * Central function to fetch data based on the selected report type.
 */
export const fetchReportData = async (reportType: string): Promise<ReportData[]> => {
  let endpoint = "";

  switch (reportType) {
    // --- HR Reports ---
    case "leaveBalance":
      endpoint = "/reports/leave-balances/";
      break;

    // --- Payroll Reports ---
    case "basicSalary":
      endpoint = "/reports/basic-salary/";
      break;
    case "paye":
      endpoint = "/reports/paye/";
      break;
    case "nssa":
      endpoint = "/reports/nssa/";
      break;
      
    // --- Placeholder for future reports ---
    // You can point these to a generic endpoint if the backend isn't ready yet
    case "medicalAid":
    case "pension":
    case "zimdef":
      // endpoint = `/reports/generic-deductions/?type=${reportType}`;
      console.warn(`Report type ${reportType} not yet implemented on backend.`);
      return []; 

    default:
      console.warn(`Unknown report type: ${reportType}`);
      return [];
  }

  try {
    const response = await apiClient.get<ReportData[]>('/hr' +endpoint );
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch ${reportType} report:`, error);
    throw error;
  }
};