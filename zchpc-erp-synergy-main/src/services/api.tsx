// src/api.js
import axios from 'axios';

// const API_URL = ''
export const API_BASE_URL = `https://zchpcerp.zchpc.ac.zw/api/v2/`;

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Automatically add the JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;

export const getPayrollRecords = (params) => api.get('payroll-records/', { params });
export const generateMonthlyPayroll = (period) => api.post('generate-monthly-payroll/', { period });
export const updatePayrollStatus = (payrollId, status) => api.post(`update-payroll-status/${payrollId}/`, { status });
export const deletePayrollSlip = (employeeId, period) => api.delete('delete-payslip/', { params: { employee_id: employeeId, period } });
export const getCurrentZigRate = () => api.get('current-rate/');

// Configuration APIs
export const getTaxBrackets = (params) => api.get('payroll/tax-brackets/', { params });
export const createTaxBracket = (data) => api.post('payroll/tax-brackets/', data);
export const updateTaxBracket = (id, data) => api.put(`payroll/tax-brackets/${id}/`, data);
export const deleteTaxBracket = (id) => api.delete(`payroll/tax-brackets/${id}/`);

export const getNSSACaps = (params) => api.get('nssa-caps/', { params });
export const createNSSACap = (data) => api.post('nssa-caps/', data);
export const updateNSSACap = (id, data) => api.put(`nssa-caps/${id}/`, data);
export const deleteNSSACap = (id) => api.delete(`nssa-caps/${id}/`);

export const getPensionFunds = () => api.get('pension-funds/');
export const createPensionFund = (data) => api.post('pension-funds/', data);
export const updatePensionFund = (id, data) => api.put(`pension-funds/${id}/`, data);
export const deletePensionFund = (id) => api.delete(`pension-funds/${id}/`);

export const getEmployeeDeductables = (params) => api.get('employee-deductables/', { params });
export const createEmployeeDeductable = (data) => api.post('employee-deductables/', data);
export const updateEmployeeDeductable = (id, data) => api.put(`employee-deductables/${id}/`, data);
export const deleteEmployeeDeductable = (id) => api.delete(`employee-deductables/${id}/`);

// Payroll Period API Calls - generates periods client-side since no backend endpoint
export const getPayrollPeriods = () => {
  // Generate last 12 months as payroll periods
  const periods = [];
  const now = new Date();
  for (let i = 0; i < 12; i++) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    periods.push({
      id: i + 1,
      period: date.toISOString().slice(0, 7),
      label: date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
    });
  }
  return Promise.resolve({ data: periods });
};
export const createPayrollPeriod = (data) => Promise.resolve({ data });
export const updatePayrollPeriod = (id, data) => Promise.resolve({ data });
export const deletePayrollPeriod = (id) => Promise.resolve({});

// NEW: Allowance and Deduction Type API Calls
export const getAllowanceTypes = () => api.get('hr/allowances/');
export const createAllowanceType = (data) => api.post('hr/allowances/', data);
export const updateAllowanceType = (id, data) => api.put(`hr/allowances/${id}/`, data);
export const deleteAllowanceType = (id) => api.delete(`hr/allowances/${id}/`);

export const getDeductionTypes = () => api.get('hr/deductions/');
export const createDeductionType = (data) => api.post('hr/deductions/', data);
export const updateDeductionType = (id, data) => api.put(`hr/deductions/${id}/`, data);
export const deleteDeductionType = (id) => api.delete(`hr/deductions/${id}/`);

export const updateSalary = (id, data) => api.post(`update-employee-salary/${id}/`, data);

// Recruitment / Job Posting APIs
export const createJobPosting = (data) => api.post('jobs/', data);
export const getJobPostings = () => api.get('jobs/');