import { apiClient } from "@/server/apiClient";

export const addDepartMethod = (payload) => {
  return apiClient.post("/hr/departments/", payload);
};

export const getDepartment = () => {
  return apiClient.get("/hr/departments/");
};
export const addUser = (data) => {
  return apiClient.post("/auth/users/", data);
};
// src/server/Server.js (or wherever deleteUser is defined)

export const deleteUserMethod = async (id) => {
    return await apiClient.delete(`/auth/users/${id}/`);
}
export const hrDashboard = () => {
    return  apiClient.get(`/hr/dashboard/`);
}



// --- Positions ---
export const getPositions = async (departmentId = null) => {
  let url = '/hr/positions/';
  if (departmentId) {
    url += `?department_id=${departmentId}`;
  }
  const response = await apiClient.get(url);
  return response.data;
};

export const addPosition = async (data) => {
  const response = await apiClient.post('/hr/positions/', data);
  return response.data;
};


export const getDeductionTypes = async () => {
  const response = await apiClient.get('/hr/deductions/');
  return response.data;
};

export const addDeductionType = async (data: { name: string; description?: string }) => {
  const response = await apiClient.post('/hr/deductions/', data);
  return response.data;
};

export const deleteDeductionType = async (id: number) => {
  await apiClient.delete(`/hr/deductions/${id}/`);
};

