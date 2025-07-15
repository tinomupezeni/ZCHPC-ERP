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
}

export default Server;
