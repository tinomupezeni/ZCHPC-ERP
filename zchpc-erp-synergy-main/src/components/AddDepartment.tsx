import { useState } from "react";
// import toast from "react-hot-toast";
// import Server from "../../server/Server";

export default function AddDepartment({ setShowModal, onSuccess }) {
  const [employee, setEmployee] = useState({
    firstname: "",
    surname: "",
    role: "",
    email: "",
    department: "",
    password: "erp@1234",
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setEmployee({ ...employee, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);

    // Server.register(employee)
    //   .then(() => {
    //     toast.success("New user successfully added");
    //     setLoading(false);
    //     onSuccess();
    //   })
    //   .catch((error) => {
    //     console.error("Error registering user:", error);
    //     toast.error("Failed to add new user");
    //     setLoading(false);
    //   });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-5 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-lg shadow-lg">
        {/* Header */}
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Add Department</h2>
          <button
            onClick={() => setShowModal(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form className="p-6 space-y-4" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 gap-4">
            <div>
              <label className="text-sm text-gray-600">Department Name</label>
              <input
                type="text"
                name="firstname"
                value={employee.firstname}
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-600">Manager</label>
              <select
                name="manager" // Ensure it matches your state structure
                value={employee.manager} // This should correspond to how manager is stored in state
                onChange={handleChange}
                required
                className="w-full p-2 border rounded"
              >
                <option value="" disabled>
                  Select a manager
                </option>
                <option value="administrator">Administrator</option>
                <option value="guest">Godffrey Marufu</option>
                <option value="general user">General Mucheche</option>
              </select>
            </div>
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
              {loading ? "Adding new department..." : "Add Department"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
