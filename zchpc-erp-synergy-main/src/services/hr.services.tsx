import apiClient from "@/services/apiClient";

// --- Departments ---
export const getDepartment = () => {
  return apiClient.get("/hr/departments/");
};

export const addDepartment = async (payload) => {
  const response = await apiClient.post("/hr/departments/", payload);
  return response.data;
};

export const updateRole = async (id, data) => {
  const response = await apiClient.patch(`/hr/roles/${id}/`, data);
  return response.data;
};

// --- Roles (The New RBAC Endpoints) ---
export const getRoles = async () => {
  const response = await apiClient.get("/hr/roles/");
  console.log(response);
  
  return response.data;
};

export const addRole = async (payload) => {
  // payload: { name: "MANAGER", display_name: "Department Manager" }
  const response = await apiClient.post("/hr/roles/", payload);
  return response.data;
};

// --- Users ---
export const addUser = async (data) => {
  // We MUST await this to send the temp_password back to the UI
  const response = await apiClient.post("/auth/users/", data);
  return response; // Return the whole response so the component can access .data
};

// Users are never deleted (AUD-02): access is ended by deactivating the login,
// which the backend applies to the employee lifecycle and authorizes itself.
export const deactivateUser = async (id) => {
  return await apiClient.patch(`/auth/users/${id}/`, { is_active: false });
};

// --- Dashboard & Analytics ---
export const hrDashboard = () => {
  return apiClient.get(`/hr/dashboard/`);
};

// --- Positions ---
export const getPositions = async (departmentId = null) => {
  let url = "/hr/positions/";
  if (departmentId) {
    url += `?department=${departmentId}`; // Matches Django filter naming
  }
  const response = await apiClient.get(url);
  return response.data;
};

export const addPosition = async (data) => {
  const response = await apiClient.post("/hr/positions/", data);
  return response.data;
};

// --- Payroll Types ---
export const getDeductionTypes = async () => {
  const response = await apiClient.get("/hr/deductions/");
  return response.data;
};

export const addDeductionType = async (data) => {
  const response = await apiClient.post("/hr/deductions/", data);
  return response.data;
};

export const deleteDeductionType = async (id) => {
  await apiClient.delete(`/hr/deductions/${id}/`);
};
