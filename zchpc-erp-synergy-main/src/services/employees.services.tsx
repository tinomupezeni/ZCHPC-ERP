import apiClient  from "@/services/apiClient";

export const addEmployee = (payload) => {
  return apiClient.post("/hr/employees/", payload);
};

export const getEmployees = () => {
  return apiClient.get("/hr/employees/");
};

export const getEmployeeById = (id: string) => {
  return apiClient.get(`/bff/employees/${id}/`);
};
export const updateEmployee = (id, data) => {
  return apiClient.patch(`/bff/employees/${id}/`, data);
};

export const deleteEmployee = (id) => {
  return apiClient.delete(`/hr/employees/${id}/`);
};
