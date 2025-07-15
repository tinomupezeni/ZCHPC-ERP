import React, { useState, useEffect } from "react";
import axios from "axios";
// import { div, Button,  Label, Select } from 'tailwind-react-ui';
import { Input } from "./ui/input";
import { toast } from "sonner";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import Server from "@/server/Server";

const EditUserModal = ({ closeModal, userId }) => {
  const [userData, setUserData] = useState({});
  const [loading, setLoading] = useState(false);

  // Fetch the user data when modal opens
  useEffect(() => {
    Server.fetchUserDetails(userId)
      .then((response) => {
        setUserData(response.data);
      })
      .catch((error) => {
        console.log(error);
      });
  }, [ userId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData({ ...userData, [name]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);

    axios
      .put(`/user/${userId}/`, userData) // API call to update the user
      .then((response) => {
        toast.success("User updated successfully!");
   
        closeModal(); // Close modal after success
      })
      .catch((error) => {
        toast.error("Error updating user");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50  flex items-center justify-center w-full">
      <form
        onSubmit={handleSubmit}
        className="p-6 bg-white rounded-lg shadow-md space-y-4 bg-white rounded-lg w-full max-w-lg shadow-lg"
      >
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Edit User details</h2>
          <button
            onClick={closeModal}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        {/* First Name */}
        <div>
          <Label htmlFor="firstname">First Name</Label>
          <Input
            id="firstname"
            name="firstname"
            value={userData.firstname}
            onChange={handleChange}
            className="mt-1"
          />
        </div>

        {/* Surname */}
        <div>
          <Label htmlFor="surname">Surname</Label>
          <Input
            id="surname"
            name="surname"
            value={userData.surname}
            onChange={handleChange}
            className="mt-1"
          />
        </div>

        {/* Email */}
        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            name="email"
            type="email"
            value={userData.email}
            onChange={handleChange}
            className="mt-1"
          />
        </div>

        {/* Role */}
        <div>
          <Label htmlFor="role">Role</Label>
          <select
            id="role"
            name="role"
            value={userData.role}
            onChange={handleChange}
            className="w-full p-2 border rounded"
          >
            <option value="admin">Admin</option>
            <option value="user">User</option>
            <option value="guest">Guest</option>
            {/* Add more roles if necessary */}
          </select>
        </div>

        {/* Department */}
        <div>
          <Label htmlFor="department">Department</Label>
          <select
            name="department" // Ensure it matches your state structure
            value={userData.department} // This should correspond to how role is stored in state
            onChange={handleChange}
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

        {/* Salary */}
        <div>
          <Label htmlFor="salary">Salary</Label>
          <Input
            id="salary"
            name="salary"
            type="number"
            value={userData.salary}
            onChange={handleChange}
            className="mt-1"
          />
        </div>

        {/* Contract From */}
        <div>
          <Label htmlFor="contractFrom">Contract From</Label>
          <Input
            id="contractFrom"
            name="contractFrom"
            type="date"
            value={userData.contractFrom}
            onChange={handleChange}
            className="mt-1"
          />
        </div>

        {/* Contract To */}
        <div>
          <Label htmlFor="contractTo">Contract To</Label>
          <Input
            id="contractTo"
            name="contractTo"
            type="date"
            value={userData.contractTo}
            onChange={handleChange}
            className="mt-1"
          />
        </div>

        {/* Modal Actions */}
        <div className="flex justify-end space-x-4 mt-4">
          <Button
            onClick={closeModal}
            variant="outline"
            className="px-4 py-2 border rounded text-gray-600 hover:bg-gray-100"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={loading}
            variant="solid"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {loading ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default EditUserModal;
