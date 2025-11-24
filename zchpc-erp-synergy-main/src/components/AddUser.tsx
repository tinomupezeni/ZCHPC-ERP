import { useState, useEffect } from "react";
import { toast } from "sonner";

import { getDepartment, addUser } from "@/server/hr.services";

export default function AddUser({ setShowModal, onSuccess }) {
  const [employee, setEmployee] = useState({
    first_name: "",
    last_name: "",
    role: "",
    email: "",
    department: "", // Ensure this is initialized to a default value for the dropdown
  });
  const [loading, setLoading] = useState(false);
  const [departments, setDepartments] = useState([]);
  const [departmentsLoading, setDepartmentsLoading] = useState(true);

  // Define a list of meaningful ERP roles
  const roles = [
  { value: "ADMIN", label: "Admin" },
  { value: "HR", label: "HR" },
  { value: "ACCOUNTANT", label: "Accountant" },
  { value: "PROCUREMENT", label: "Procurement" },
  { value: "SALES", label: "Sales" },
  { value: "MANAGER", label: "Manager" },
  { value: "STAFF", label: "Staff" },
  { value: "INTERN", label: "Intern" },
];


  // Fetch departments when the component loads
  useEffect(() => {
    getDepartment()
      .then((response) => {
        setDepartments(response.data);
      })
      .catch((error) => {
        console.error("Failed to fetch departments:", error);
        toast.error("Failed to load departments.");
      })
      .finally(() => {
        setDepartmentsLoading(false);
      });
  }, []);

  const handleChange = (e) => {
    setEmployee({ ...employee, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);

    addUser(employee)
      .then(() => {
        toast.success("New user successfully added");
        setLoading(false);
        onSuccess();
        setShowModal(false);
      })
      .catch((error) => {
        console.error("Error registering user:", error.response.data);
        const errorMessage = error.response?.data?.email?.[0] || "Failed to add new user. Please check your inputs.";
        toast.error(errorMessage);
        setLoading(false);
      });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg w-full max-w-lg shadow-lg">
        {/* Header */}
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Add System User</h2>
          <button
            onClick={() => setShowModal(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form className="p-6 space-y-4" onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-600">First Name</label>
              <input
                type="text"
                name="first_name"
                value={employee.first_name}
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600">Surname</label>
              <input
                type="text"
                name="last_name"
                value={employee.last_name}
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-600">Role</label>
              <select
                name="role"
                value={employee.role}
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
              >
                <option value="" disabled>Select a role</option>
                {roles.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-600">Department</label>
              <select
                name="department"
                value={employee.department}
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
                disabled={departmentsLoading}
              >
                <option value="" disabled>
                  {departmentsLoading ? "Loading..." : "Select Department"}
                </option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm text-gray-600">Email</label>
            <input
              type="email"
              name="email"
              value={employee.email}
              onChange={handleChange}
              required
              className="w-full p-2 border rounded"
            />
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-3 mt-4">
            <button
              type="button"
              onClick={() => setShowModal(false)}
              className="px-4 py-2 border rounded text-gray-600 hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || departmentsLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? "Adding user..." : "Add User"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}