import apiClient  from "@/services/apiClient";

export const addEmployee = (payload) => {
  return apiClient.post("/hr/employees/", payload);
};

// Active employees only, unless includeInactive: HR's own list also shows
// deactivated ones, so they can be reactivated (archived ones never).
export const getEmployees = ({ includeInactive = false } = {}) => {
  return apiClient.get("/hr/employees/", {
    params: includeInactive ? { include_inactive: "true" } : undefined,
  });
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

// Deactivate (AUD-02 soft delete): ends the employee's ERP and Portal sign-in.
export const deactivateEmployee = (id: number | string) => {
  return apiClient.delete(`/hr/employees/${id}/`);
};

// Back to active with the same record; a re-enabled login comes back with a
// one-time temporary_password (REM-07), null when none was re-enabled.
export const reactivateEmployee = (id: number | string) => {
  return apiClient.post(`/hr/employees/${id}/reactivate/`, {});
};
