import axios from "axios";

const api_url = "http://127.0.0.1:8000/";
// const api_url = "http://0.0.0.0:8000/";
// const api_url = "http://192.168.80.92:8000/";

const getAuthHeaders = () => {
  // Implement logic to get your auth token (e.g., from localStorage or a global state)
  // const token = localStorage.getItem('authToken');
  // return token ? { Authorization: `Bearer ${token}` } : {};
  return {}; // For now, empty if no auth
};

  interface TrainingProgramUpdateData {
    title: "",
    category: "",
    duration: "",
    mandatory: false,
  }

class Server {
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
  }

  // fetching all training programs 
  static getTrainingPrograms= () => {
    return axios.get(`${api_url}all/training/programs/`);
  }

  //delete training program
  static deleteTrainingProgram = (id) => {
    return axios.delete(`${api_url}delete/training/program/${id}/`);
  }

  //update training program
  static updateTrainingProgram = (id: number, data: TrainingProgramUpdateData) => {
    return axios.put(`${api_url}update/training/program/${id}/`, data);
  }

  // add training session
  static addTrainingSession = (data) => {
    return axios.post(`${api_url}training/sessions/`, data);
  }
  // fetch all training sessions
  static getTrainingSessions = () => {
    return axios.get(`${api_url}training/sessions/`);
  }
  // delete training session
  static deleteTrainingSession = (id) => {
    return axios.delete(`${api_url}training/sessions/${id}/`);
  }
  // update training session
  static updateTrainingSession = (id, data) => {
    return axios.put(`${api_url}training/sessions/${id}/`, data);
  }

  // add training enrollment
  static addTrainingEnrollment = (data) => {
    return axios.post(`${api_url}training/enrollments/`, data);
  }
  // fetch all training enrollments
  static getTrainingEnrollments = () => {
    return axios.get(`${api_url}training/enrollments/`);
  }
  // delete training enrollment
  static deleteTrainingEnrollment = (id) => {
    return axios.delete(`${api_url}training/enrollments/${id}/`);
  }
  // update training enrollment
  static updateTrainingEnrollment = (id, data) => {
    return axios.put(`${api_url}training/enrollments/${id}/`, data);
  }

  // add training certification
  static addTrainingCertification = (data) => {
    return axios.post(`${api_url}training/certifications/`, data);
  }
  // fetch all training certifications
  static getTrainingCertifications = () => {
    return axios.get(`${api_url}training/certifications/`);
  }
  // delete training certification
  static deleteTrainingCertification = (id) => {
    return axios.delete(`${api_url}training/certifications/${id}/`);
  }
  // update training certification
  static updateTrainingCertification = (id, data) => {
    return axios.put(`${api_url}training/certifications/${id}/`, data);
  }
  // search training certifications
  static searchTrainingCertifications = (searchTerm) => {
    return axios.get(`${api_url}training/certifications/search/?search=${searchTerm}`);
  }


}

export default Server;
