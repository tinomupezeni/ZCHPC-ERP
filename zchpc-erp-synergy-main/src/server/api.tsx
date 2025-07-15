// src/api.js
import axios from 'axios';

const API_BASE_URL = "http://127.0.0.1:8000/"; // Replace with your Django backend URL

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const getPayrollRecords = (params) => api.get('payroll-records/', { params });
export const generateMonthlyPayroll = (period) => api.post('generate-monthly-payroll/', { period });
export const updatePayrollStatus = (payrollId, status) => api.post(`update-payroll-status/${payrollId}/`, { status });
export const deletePayrollSlip = (employeeId, period) => api.delete('delete-payslip/', { params: { employee_id: employeeId, period } });
export const getCurrentZigRate = () => api.get('current-rate/');

// Configuration APIs
export const getTaxBrackets = (params) => api.get('tax-brackets/', { params });
export const createTaxBracket = (data) => api.post('tax-brackets/', data);
export const updateTaxBracket = (id, data) => api.put(`tax-brackets/${id}/`, data);
export const deleteTaxBracket = (id) => api.delete(`tax-brackets/${id}/`);

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

// Payroll Period API Calls (CORRECTED)
export const getPayrollPeriods = () => api.get('payroll-periods/'); // No need for `${api}`
export const createPayrollPeriod = (data) => api.post('payroll-periods/', data);
export const updatePayrollPeriod = (id, data) => api.put(`payroll-periods/${id}/`, data);
export const deletePayrollPeriod = (id) => api.delete(`payroll-periods/${id}/`);

// NEW: Allowance and Deduction Type API Calls
export const getAllowanceTypes = () => api.get('allowance-types/');
export const createAllowanceType = (data) => api.post('allowance-types/', data);
export const updateAllowanceType = (id, data) => api.put(`allowance-types/${id}/`, data);
export const deleteAllowanceType = (id) => api.delete(`allowance-types/${id}/`);

export const getDeductionTypes = () => api.get('deduction-types/');
export const createDeductionType = (data) => api.post('deduction-types/', data);
export const updateDeductionType = (id, data) => api.put(`deduction-types/${id}/`, data);
export const deleteDeductionType = (id) => api.delete(`deduction-types/${id}/`);

export const updateSalary = (id, data) => api.post(`update-employee-salary/${id}/`, data);