
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
    return apiClient.get(`${api_url}rates/`);
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
    return apiClient.get(`${api_url}all/attendance/`);
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

  // delete biometric record
  static fetchLogs = () => {
    return apiClient.get(`${api_url}/auth/logs/`, {
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
    return apiClient.get(`${api_url}api/payroll/payrolls/?period=${month}`);
  };

  // delete payslip
  static deleteEmployeeSlip = (id, period) => {
    return apiClient.delete(
      `${api_url}/payrolls/delete_slip/?employee=${id}&period=${period}`
    );
  };

  // approve payslip
static approvePayslip = (id, period) => {
  return apiClient.post(
    `${api_url}api/payroll/payrolls/approve_slip/`,
    { employee: id, period: period }, // send data in body
    { headers: getAuthHeaders() }
  );
};


  // API's for hr training and development

  //adding  training program
  static addTrainingProgram = (data) => {
    return apiClient.post(`${api_url}register/training/program/`, data);
  };

  // fetching all training programs
  static getTrainingPrograms = () => {
    return apiClient.get(`${api_url}all/training/programs/`);
  };

  //delete training program
  static deleteTrainingProgram = (id) => {
    return apiClient.delete(`${api_url}delete/training/program/${id}/`);
  };

  //update training program
  static updateTrainingProgram = (
    id: number,
    data: TrainingProgramUpdateData
  ) => {
    return apiClient.put(`${api_url}update/training/program/${id}/`, data);
  };

  // add training session
  static addTrainingSession = (data) => {
    return apiClient.post(`${api_url}training/sessions/`, data);
  };
  // fetch all training sessions
  static getTrainingSessions = () => {
    return apiClient.get(`${api_url}training/sessions/`);
  };
  // delete training session
  static deleteTrainingSession = (id) => {
    return apiClient.delete(`${api_url}training/sessions/${id}/`);
  };
  // update training session
  static updateTrainingSession = (id, data) => {
    return apiClient.put(`${api_url}training/sessions/${id}/`, data);
  };

  // add training enrollment
  static addTrainingEnrollment = (data) => {
    return apiClient.post(`${api_url}training/enrollments/`, data);
  };
  // fetch all training enrollments
  static getTrainingEnrollments = () => {
    return apiClient.get(`${api_url}training/enrollments/`);
  };
  // delete training enrollment
  static deleteTrainingEnrollment = (id) => {
    return apiClient.delete(`${api_url}training/enrollments/${id}/`);
  };
  // update training enrollment
  static updateTrainingEnrollment = (id, data) => {
    return apiClient.put(`${api_url}training/enrollments/${id}/`, data);
  };

  // add training certification
  static addTrainingCertification = (data) => {
    return apiClient.post(`${api_url}training/certifications/`, data);
  };
  // fetch all training certifications
  static getTrainingCertifications = () => {
    return apiClient.get(`${api_url}training/certifications/`);
  };
  // delete training certification
  static deleteTrainingCertification = (id) => {
    return apiClient.delete(`${api_url}training/certifications/${id}/`);
  };
  // update training certification
  static updateTrainingCertification = (id, data) => {
    return apiClient.put(`${api_url}training/certifications/${id}/`, data);
  };
  // search training certifications
  static searchTrainingCertifications = (searchTerm) => {
    return apiClient.get(
      `${api_url}training/certifications/search/?search=${searchTerm}`
    );
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

}

export default Server;
