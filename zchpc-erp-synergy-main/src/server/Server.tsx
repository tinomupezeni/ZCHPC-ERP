import axios from "axios";

const api_url = "http://127.0.0.1:8000/";
// const api_url = "http://0.0.0.0:8000/";
// const api_url = "http://192.168.80.92:8000/";
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  console.log(token);
  
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

  
  
  static login = (email, password) => {
    // This POST request should go to your login endpoint
    return axios.post(`${api_url}token/`, { username: email, password });
  };

  // Optional: A method to refresh the token
  static refreshToken = (refresh_token) => {
    return axios.post(`${api_url}token/refresh/`, { refresh: refresh_token });
  };

  static fetchUserDetailsFromToken = () => {
    return axios.get(`${api_url}user-details/`, {
      headers: getAuthHeaders(),
    });
  };

  // add system user in settings view
  static addSystemUSer = (data) => {
    return axios.post(`${api_url}register/user/`, data);
  };

  //   fetch all available usrs in the settings view
  static fetchUser = () => {
    return axios.get(`${api_url}all/users/`);
  };

  //   delete a user in settings
  static deleteUser = (id) => {
    return axios.delete(`${api_url}delete/user/${id}/`);
  };
  //   fetch a user in settings
  static fetchUserDetails = (id) => {
    return axios.get(`${api_url}get/user/${id}/`);
  };

  //   update user settings
  static updateSystemUSer = (data) => {
    return axios.post(`${api_url}update/user/`, data);
  };

   // fetch attendance records
  static fetchAttendanceRecords = () => {
    return axios.get(`${api_url}all/attendance/`);
  };

  // delete attendance record
  static deleteAttendanceRecord = (id) => {
    return axios.delete(`${api_url}delete/attendance/${id}/`);
  };

    // fetch biometric records
  static fetchBiometricRecords = () => {
    return axios.get(`${api_url}all/biometric/`);
  };

  // delete biometric record
  static deleteBiometricRecord = (id) => {
    return axios.delete(`${api_url}delete/biometric/${id}/`);
  };

  // static updatePayroll

  //------------ hr
  // add employee
  static addEmployee = (data) => {
    return axios.post(`${api_url}register/employee/`, data);
  };
  // fetch all employees
  static fetchEmployees = () => {
    return axios.get(`${api_url}all/employees/`);
  };

  // fetch payslips
  static fetchPayslips = (month) => {
    return axios.get(`${api_url}all/payslips/?period=${month}`);
  };

  // delete payslip
  static deleteEmployeeSlip = (id, period) => {
    return axios.delete(
      `${api_url}/delete/payslip/?employee=${id}&period=${period}`
    );
  };

  // API's for hr training and development

  //adding  training program
  static addTrainingProgram = (data) => {
    return axios.post(`${api_url}register/training/program/`, data);
  };

  // fetching all training programs
  static getTrainingPrograms = () => {
    return axios.get(`${api_url}all/training/programs/`);
  };

  //delete training program
  static deleteTrainingProgram = (id) => {
    return axios.delete(`${api_url}delete/training/program/${id}/`);
  };

  //update training program
  static updateTrainingProgram = (
    id: number,
    data: TrainingProgramUpdateData
  ) => {
    return axios.put(`${api_url}update/training/program/${id}/`, data);
  };

  // add training session
  static addTrainingSession = (data) => {
    return axios.post(`${api_url}training/sessions/`, data);
  };
  // fetch all training sessions
  static getTrainingSessions = () => {
    return axios.get(`${api_url}training/sessions/`);
  };
  // delete training session
  static deleteTrainingSession = (id) => {
    return axios.delete(`${api_url}training/sessions/${id}/`);
  };
  // update training session
  static updateTrainingSession = (id, data) => {
    return axios.put(`${api_url}training/sessions/${id}/`, data);
  };

  // add training enrollment
  static addTrainingEnrollment = (data) => {
    return axios.post(`${api_url}training/enrollments/`, data);
  };
  // fetch all training enrollments
  static getTrainingEnrollments = () => {
    return axios.get(`${api_url}training/enrollments/`);
  };
  // delete training enrollment
  static deleteTrainingEnrollment = (id) => {
    return axios.delete(`${api_url}training/enrollments/${id}/`);
  };
  // update training enrollment
  static updateTrainingEnrollment = (id, data) => {
    return axios.put(`${api_url}training/enrollments/${id}/`, data);
  };

  // add training certification
  static addTrainingCertification = (data) => {
    return axios.post(`${api_url}training/certifications/`, data);
  };
  // fetch all training certifications
  static getTrainingCertifications = () => {
    return axios.get(`${api_url}training/certifications/`);
  };
  // delete training certification
  static deleteTrainingCertification = (id) => {
    return axios.delete(`${api_url}training/certifications/${id}/`);
  };
  // update training certification
  static updateTrainingCertification = (id, data) => {
    return axios.put(`${api_url}training/certifications/${id}/`, data);
  };
  // search training certifications
  static searchTrainingCertifications = (searchTerm) => {
    return axios.get(
      `${api_url}training/certifications/search/?search=${searchTerm}`
    );
  };
  // ----------------- Department CRUD -------------------

  /**
   * Creates a new department.
   * @param {object} data The department data (name, description, head).
   * @returns {Promise} The axios promise.
   */
  static addDepartment = (data) => {
    return axios.post(`${api_url}departments/`, data, {
      headers: getAuthHeaders(),
    });
  };

  /**
   * Fetches a list of all departments.
   * @returns {Promise} The axios promise.
   */
  static fetchDepartments = () => {
    return axios.get(`${api_url}departments/`, { headers: getAuthHeaders() });
  };

  /**
   * Fetches the details of a single department.
   * @param {number} id The ID of the department.
   * @returns {Promise} The axios promise.
   */
  static fetchDepartmentDetails = (id) => {
    return axios.get(`${api_url}departments/${id}/`, {
      headers: getAuthHeaders(),
    });
  };

  /**
   * Updates an existing department.
   * @param {number} id The ID of the department to update.
   * @param {object} data The updated department data (name, description, head).
   * @returns {Promise} The axios promise.
   */
  static updateDepartment = (id, data) => {
    // Use PUT for full update or PATCH for partial update.
    // DRF ModelViewSet handles both. Let's use PUT for a full update.
    return axios.put(`${api_url}departments/${id}/`, data, {
      headers: getAuthHeaders(),
    });
  };

  /**
   * Deletes a department.
   * @param {number} id The ID of the department to delete.
   * @returns {Promise} The axios promise.
   */
  static deleteDepartment = (id) => {
    return axios.delete(`${api_url}departments/${id}/`, {
      headers: getAuthHeaders(),
    });
  };

  // Admin Dashboard Data
  static fetchDashboardData = () => {
    return axios.get(`${api_url}dashboard-data/`, {
      headers: getAuthHeaders(),
    });
  }

  // Admin Dashboard Data
  static fetchHrDashboardData = () => {
    return axios.get(`${api_url}hr-dashboard/`, {
      headers: getAuthHeaders(),
    });
  }
}

export default Server;
