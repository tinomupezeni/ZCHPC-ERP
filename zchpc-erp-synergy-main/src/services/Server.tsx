
import { API_BASE_URL } from "./api";
import apiClient  from "./apiClient";

const api_url = API_BASE_URL

const getAuthHeaders = () => {
  const token = localStorage.getItem("access_token");

  // Implement logic to get your auth token (e.g., from localStorage or a global state)
  // const token = localStorage.getItem('authToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

interface TrainingProgramUpdateData {
  title: "";
  category: "";
  duration: "";
  mandatory: false;
}

class Server {
  static getCurrencyRates() {
    return apiClient.get(`${api_url}payroll/rates/`);
  }

  static addCurrencyRate(data: { date: string; zigRate: number }) {
    return apiClient.post(`${api_url}payroll/rates/`, data);
  }

  static fetchLatestRate() {
    return apiClient.post(`${api_url}payroll/rates/fetch_latest/`);
  }
  static login = (email, password) => {
    // This POST request should go to your login endpoint
    return apiClient.post(`${api_url}token/`, { email, password });
  };

  // Optional: A method to refresh the token
  static refreshToken = (refresh_token) => {
    return apiClient.post(`${api_url}token/refresh/`, { refresh: refresh_token });
  };

  static fetchUserDetailsFromToken = () => {
    return apiClient.get(`${api_url}user-details/`, {
      headers: getAuthHeaders(),
    });
  };

  

 
  //   fetch a user in settings
  static fetchUserDetails = (id) => {
    return apiClient.get(`${api_url}get/user/${id}/`);
  };

  //   update user settings
  static updateSystemUSer = (data) => {
    return apiClient.post(`${api_url}update/user/`, data);
  };

  // fetch attendance records
  static fetchAttendanceRecords = () => {
    return apiClient.get(`${api_url}attendance/history/`);
  };

  // delete attendance record
  static deleteAttendanceRecord = (id) => {
    return apiClient.delete(`${api_url}delete/attendance/${id}/`);
  };

  // fetch biometric records
  static fetchBiometricRecords = () => {
    return apiClient.get(`${api_url}all/biometric/`);
  };

  // delete biometric record
  static deleteBiometricRecord = (id) => {
    return apiClient.delete(`${api_url}delete/biometric/${id}/`);
  };

  // fetch audit logs
  static fetchLogs = () => {
    return apiClient.get(`${api_url}auth/logs/`, {
      headers: getAuthHeaders(),
    });
  };

  // static updatePayroll

  //------------ hr
  // add employee
  static addEmployee = (data) => {
    return apiClient.post(`${api_url}register/employee/`, data);
  };
  // fetch all employees


  // fetch payslips
  static fetchPayslips = (month) => {
    return apiClient.get(`${api_url}payroll/payslips/?period=${month}`);
  };

  // delete payslip
  static deleteEmployeeSlip = (id, period) => {
    return apiClient.delete(
      `${api_url}payroll/payslips/${id}/`
    );
  };

  // approve payslip
static approvePayslip = (id, period) => {
  return apiClient.post(
    `${api_url}payroll/payslips/${id}/approve/`,
    { employee: id, period: period }, // send data in body
    { headers: getAuthHeaders() }
  );
};


  // API's for hr training and development

  //adding  training program - TODO: Training module not implemented yet
  static addTrainingProgram = (data) => {
    return Promise.resolve({ data: { id: Date.now(), ...data } });
  };

  // fetching all training programs - TODO: Training module not implemented yet
  static getTrainingPrograms = () => {
    // Return empty array until training module is implemented
    return Promise.resolve({ data: [] });
  };

  // TODO: Training module not implemented yet - all training methods return mock data
  static deleteTrainingProgram = (id) => {
    return Promise.resolve({});
  };

  static updateTrainingProgram = (
    id: number,
    data: TrainingProgramUpdateData
  ) => {
    return Promise.resolve({ data: { id, ...data } });
  };

  static addTrainingSession = (data) => {
    return Promise.resolve({ data: { id: Date.now(), ...data } });
  };

  static getTrainingSessions = () => {
    return Promise.resolve({ data: [] });
  };

  static deleteTrainingSession = (id) => {
    return Promise.resolve({});
  };

  static updateTrainingSession = (id, data) => {
    return Promise.resolve({ data: { id, ...data } });
  };

  static addTrainingEnrollment = (data) => {
    return Promise.resolve({ data: { id: Date.now(), ...data } });
  };

  static getTrainingEnrollments = () => {
    return Promise.resolve({ data: [] });
  };

  static deleteTrainingEnrollment = (id) => {
    return Promise.resolve({});
  };

  static updateTrainingEnrollment = (id, data) => {
    return Promise.resolve({ data: { id, ...data } });
  };

  static addTrainingCertification = (data) => {
    return Promise.resolve({ data: { id: Date.now(), ...data } });
  };

  static getTrainingCertifications = () => {
    return Promise.resolve({ data: [] });
  };

  static deleteTrainingCertification = (id) => {
    return Promise.resolve({});
  };

  static updateTrainingCertification = (id, data) => {
    return Promise.resolve({ data: { id, ...data } });
  };

  static searchTrainingCertifications = (searchTerm) => {
    return Promise.resolve({ data: [] });
  };

  // Upload attendance records from file
  static uploadAttendance = (file) => {
    const formData = new FormData();
    formData.append("file", file);

    return apiClient.post(`${api_url}upload/attendance/`, formData, {
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "multipart/form-data",
      },
    });
  };
  // ----------------- Department CRUD -------------------

  /**
   * Fetches the details of a single department.
   * @param {number} id The ID of the department.
   * @returns {Promise} The apiClient promise.
   */
  static fetchDepartmentDetails = (id) => {
    return apiClient.get(`${api_url}departments/${id}/`, {
      headers: getAuthHeaders(),
    });
  };

  /**
   * Updates an existing department.
   * @param {number} id The ID of the department to update.
   * @param {object} data The updated department data (name, description, head).
   * @returns {Promise} The apiClient promise.
   */
  static updateDepartment = (id, data) => {
    // Use PUT for full update or PATCH for partial update.
    // DRF ModelViewSet handles both. Let's use PUT for a full update.
    return apiClient.put(`${api_url}departments/${id}/`, data, {
      headers: getAuthHeaders(),
    });
  };

  /**
   * Deletes a department.
   * @param {number} id The ID of the department to delete.
   * @returns {Promise} The apiClient promise.
   */
  static deleteDepartment = (id) => {
    return apiClient.delete(`${api_url}departments/${id}/`, {
      headers: getAuthHeaders(),
    });
  };

  // Admin Dashboard Data
  static fetchDashboardData = () => {
    return apiClient.get(`${api_url}dashboard-data/`, {
      headers: getAuthHeaders(),
    });
  };

  // Update employee deductions
  static updateEmployeeDeductions = (employeeId: number | string, data: any) => {
    return apiClient.post(`${api_url}hr/employees/${employeeId}/deductions/`, data, {
      headers: getAuthHeaders(),
    });
  };

  // Update employee allowances
  static updateEmployeeAllowances = (employeeId: number | string, data: any) => {
    return apiClient.post(`${api_url}hr/employees/${employeeId}/allowances/`, data, {
      headers: getAuthHeaders(),
    });
  };

}

export default Server;
