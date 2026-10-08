import apiClient  from "@/services/apiClient";

export const addEmployee = (payload) => {
  return apiClient.post("/hr/employees/", payload);
};

export const getEmployees = () => {
  return apiClient.get("/hr/employees/");
};

// The HR employee record, by its integer id (Employees.id from GET /hr/employees/).
export const getEmployeeById = (id: number | string) => {
  return apiClient.get(`/hr/employees/${id}/`);
};
// Partial update: send only the fields that changed - the backend authorizes
// each field it receives (AUD-02).
export const updateEmployee = (id: number | string, data) => {
  return apiClient.patch(`/hr/employees/${id}/`, data);
};

export const deleteEmployee = (id) => {
  return apiClient.delete(`/hr/employees/${id}/`);
};
