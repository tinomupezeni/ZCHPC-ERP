import { useState, useEffect } from "react";
import {toast} from "sonner";
import Server from "../server/Server";
import { on } from "events";

export default function AddDepartment({ setShowModal, onSuccess }) {
  // Use state to manage department data
  const [department, setDepartment] = useState({
    name: "",
    description: "",
    department_head: null, // The ID of the CustomUser
  });
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState([]); // State to hold the list of users for the dropdown

  // Fetch the list of users when the component mounts
  useEffect(() => {
    // Assuming you have a fetchUsers method in your Server class
    // that gets all CustomUsers
    Server.fetchUser() // This needs to be the method that fetches all users
      .then((res) => {
        setUsers(res.data);
      })
      .catch((error) => {
        console.error("Error fetching users:", error);
        toast.error("Failed to load users for manager selection.");
      });
  }, []);

  const handleChange = (e) => {
    // Update the department state based on form input
    setDepartment({ ...department, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);

    // Call the new addDepartment method from your Server class
    Server.addDepartment(department)
      .then(() => {
        toast.success("New department successfully added.");
        setLoading(false);
        onSuccess()
      })
      .catch((error) => {
        console.error("Error adding department:", error);
        // Display a more informative error message if possible
        const errorMessage = error.response?.data?.name?.[0] || "Failed to add department.";
        toast.error(errorMessage);
        setLoading(false);
      });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-lg shadow-lg">
        {/* Header */}
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Add Department</h2>
          <button
            onClick={() => setShowModal(false)}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
          >
            &times; {/* Use &times; for a cleaner 'x' */}
          </button>
        </div>

        {/* Form */}
        <form className="p-6 space-y-4" onSubmit={handleSubmit}>
          {/* Department Name */}
          <div>
            <label htmlFor="name" className="text-sm text-gray-600 block mb-1">
              Department Name
            </label>
            <input
              type="text"
              name="name"
              id="name"
              value={department.name}
              onChange={handleChange}
              required
              className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Description (optional) */}
          <div>
            <label
              htmlFor="description"
              className="text-sm text-gray-600 block mb-1"
            >
              Description
            </label>
            <textarea
              name="description"
              id="description"
              value={department.description}
              onChange={handleChange}
              className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Department Head */}
          {/* <div>
            <label htmlFor="head" className="text-sm text-gray-600 block mb-1">
              Department Head
            </label>
            <select
              name="head"
              id="head"
              value={department.head || ""}
              onChange={handleChange}
              className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select a Head --</option>
              {/* Populate options from the fetched users */}
              {/* {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.first_name} {user.last_name}
                </option>
              ))}
            </select>
          </div> */} 

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
              className={`px-4 py-2 text-white rounded ${
                loading ? "bg-blue-400" : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              {loading ? "Adding Department..." : "Add Department"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}