import { useState } from "react";
import { toast } from "sonner";
import Server from "../server/Server"

export default function AddUser({ setShowModal, onSuccess }) {
  const [employee, setEmployee] = useState({
    firstname: "",
    surname: "",
    role: "",
    email: "",
    department: '',
    password: "erp@1234",
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setEmployee({ ...employee, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);

    Server.addSystemUSer(employee)
      .then(() => {
        toast.success("New user successfully added");
        setLoading(false);
        onSuccess();
        setShowModal()
      })
      .catch((error) => {
        console.error("Error registering user:", error);
        toast.error("Failed to add new user");
        setLoading(false);
      });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50  flex items-center justify-center ">
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
              <label className="text-sm text-gray-600">Name</label>
              <input
                type="text"
                name="firstname"
                value={employee.firstname}
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600">Surname</label>
              <input
                type="text"
                name="surname"
                value={employee.surname}
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
                name="role" // Ensure it matches your state structure
                value={employee.role} // This should correspond to how role is stored in state
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
              >
                <option value="" disabled>
                  Select a role
                </option>
                <option value="administrator">Administrator</option>
                <option value="guest">Guest</option>
                <option value="general user">General User</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-600">Department</label>
              <select
                name="department" // Ensure it matches your state structure
                value={employee.department} // This should correspond to how role is stored in state
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
              >
                <option value="" disabled>
                  Select Department
                </option>
                <option value="management">Management</option>
                <option value="guest">Sales</option>
                <option value="operations">Operations</option>
                <option value="operations">Finance</option>
                <option value="operations">Purchasing</option>
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
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {loading ? "Adding new user..." : "Add User"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
