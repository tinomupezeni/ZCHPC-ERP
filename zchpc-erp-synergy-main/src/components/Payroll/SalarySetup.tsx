import React, { useState, useEffect } from "react";
import {
  DollarSign,
  Plus,
  Search,
  Trash2,
  Edit2,
  Check,
  X,
  Loader,
} from "lucide-react"; // ChevronDown removed as not used
import Server from "@/server/Server"; // Assuming Server.fetchEmployees() and Server.updateSalary() are here
import { getAllowanceTypes, getDeductionTypes, updateSalary } from '../../server/api'; // Import new API functions
import { formatUSD, formatZIG } from "../ui/utils";
import { toast } from "sonner";

const SalarySetup = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [editMode, setEditMode] = useState(null); // Tracks which employee is being edited

  // formData will now track IDs of selected allowances/deductions
  const [formData, setFormData] = useState({
    usd_salary: "",
    zig_salary: "",
    // allowances and deductions will now store objects {id, name, amount} from backend for display
    // but when sending to backend, we'll convert to list of IDs.
    allowances: [],
    deductions: [],
  });

  // State for available types fetched from DB
  const [availableAllowances, setAvailableAllowances] = useState([]);
  const [availableDeductions, setAvailableDeductions] = useState([]);

  // State for the currently selected ID in the dropdown for adding
  const [selectedAllowanceTypeId, setSelectedAllowanceTypeId] = useState("");
  const [selectedDeductionTypeId, setSelectedDeductionTypeId] = useState("");

  // Fetch initial data on mount (employees, allowance types, deduction types)
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [employeesResponse, allowancesResponse, deductionsResponse] =
        await Promise.all([
          Server.fetchEmployees(), // Fetches employee data, including their linked allowances/deductions
          getAllowanceTypes(),      // Fetches all available allowance types with their preset amounts
          getDeductionTypes(),      // Fetches all available deduction types with their preset amounts
        ]);
        console.log(employeesResponse.data);
        
      setEmployees(employeesResponse.data);
      // Assuming your API returns 'results' if paginated, else direct data
      setAvailableAllowances(allowancesResponse.data.results || allowancesResponse.data);
      setAvailableDeductions(deductionsResponse.data.results || deductionsResponse.data);
    } catch (error) {
      toast.error("Failed to load setup data. Check console for details.");
      console.error("Error fetching initial setup data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Filter employees by search term
  const filteredEmployees = employees.filter(
    (emp) =>
      emp.surname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.employeeid?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Toggle edit mode for an employee
  const handleEdit = (employee) => {
    setEditMode(employee.employeeid);
    setFormData({
      usd_salary: employee.usd_salary || "",
      zig_salary: employee.zig_salary || "",
      // When editing, load the employee's current allowances/deductions
      // These are already objects with {id, name, amount} due to nested serializer
      allowances: employee.allowances || [],
      deductions: employee.deductions || [],
    });
    // Reset selection for adding new items
    setSelectedAllowanceTypeId("");
    setSelectedDeductionTypeId("");
  };

  // Cancel editing
  const handleCancel = () => {
    setEditMode(null);
    setFormData({
      usd_salary: "",
      zig_salary: "",
      allowances: [],
      deductions: [],
    });
    setSelectedAllowanceTypeId("");
    setSelectedDeductionTypeId("");
  };

  // Save changes to an employee's salary
  const handleSave = async (employeeId) => {
    console.log(employeeId);
    console.log(employees);
    
    
    if (!formData.usd_salary || !formData.zig_salary) {
      toast.error("Base salary (USD/ZIG) is required");
      return;
    }

    setLoading(true);
    try {
      const dataToSave = {
        ...formData,
        usd_salary: parseFloat(formData.usd_salary),
        zig_salary: parseFloat(formData.zig_salary),
        // NEW: Send only the IDs of allowances and deductions back to the server
        allowance_ids: formData.allowances.map(item => item.id),
        deduction_ids: formData.deductions.map(item => item.id),
      };

      // Remove the full allowance/deduction objects from the payload
      // as we only send IDs for ManyToMany updates.
      // delete dataToSave.allowances;
      // delete dataToSave.deductions;

      console.log(dataToSave);
      

      await updateSalary(employeeId, dataToSave);
      toast.success("Salary updated successfully");
      fetchInitialData(); // Refresh all data to get latest relationships
      setEditMode(null);
    } catch (error) {
      toast.error("Failed to update salary. Check console for details.");
      console.error("Error updating salary:", error.response?.data || error.message);
    } finally {
      setLoading(false);
    }
  };

  // Add a new allowance (now based only on selected type ID)
  const addAllowance = () => {
    if (!selectedAllowanceTypeId) {
      toast.error("Please select an allowance type.");
      return;
    }
    const allowanceTypeToAdd = availableAllowances.find(
      (a) => String(a.id) === String(selectedAllowanceTypeId)
    );
    if (!allowanceTypeToAdd) {
      toast.error("Selected allowance type not found.");
      return;
    }

    // Prevent adding the same allowance type multiple times
    if (formData.allowances.some(a => a.id === allowanceTypeToAdd.id)) {
        toast.error(`${allowanceTypeToAdd.name} is already added for this employee.`);
        return;
    }

    setFormData((prev) => ({
      ...prev,
      allowances: [
        ...prev.allowances,
        // Add the full allowance type object to formData for display
        // It has id, name, and amount
        allowanceTypeToAdd,
      ],
    }));
    setSelectedAllowanceTypeId(""); // Reset selected ID
  };

  // Add a new deduction (now based only on selected type ID)
  const addDeduction = () => {
    if (!selectedDeductionTypeId) {
      toast.error("Please select a deduction type.");
      return;
    }
    const deductionTypeToAdd = availableDeductions.find(
      (d) => String(d.id) === String(selectedDeductionTypeId)
    );
    if (!deductionTypeToAdd) {
      toast.error("Selected deduction type not found.");
      return;
    }

    // Prevent adding the same deduction type multiple times
    if (formData.deductions.some(d => d.id === deductionTypeToAdd.id)) {
        toast.error(`${deductionTypeToAdd.name} is already added for this employee.`);
        return;
    }

    setFormData((prev) => ({
      ...prev,
      deductions: [
        ...prev.deductions,
        // Add the full deduction type object to formData for display
        // It has id, name, and amount
        deductionTypeToAdd,
      ],
    }));
    setSelectedDeductionTypeId(""); // Reset selected ID
  };

  // Remove an allowance/deduction
  const removeItem = (type, idToRemove) => {
    // Filter by ID, not index, for robustness
    const updatedItems = formData[type].filter(item => item.id !== idToRemove);
    setFormData({ ...formData, [type]: updatedItems });
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Salary Setup</h1>
          <p className="text-sm text-gray-500">
            Configure base salaries, allowances, and deductions
          </p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Search employees..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Employee Salary Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Employee
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Current Base Salary
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Allowances
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Deductions
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan="5" className="px-6 py-8 text-center">
                  <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                  <p className="mt-2 text-sm text-gray-500">
                    Loading employee data...
                  </p>
                </td>
              </tr>
            ) : filteredEmployees.length > 0 ? (
              filteredEmployees.map((employee) => (
                // Use employee.id for key as it's more stable
                <tr key={employee.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                        {employee.firstname
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                        {employee.surname
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {employee.firstname} {employee.surname}
                        </div>
                        <div className="text-sm text-gray-500">
                          {employee.position} • {employee.department}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Base Salary */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editMode === employee.employeeid ? (
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">USD</span>
                          <input
                            type="number"
                            className="w-24 px-2 py-1 border rounded"
                            value={formData.usd_salary}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                usd_salary: e.target.value,
                              })
                            }
                          />
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">ZIG</span>
                          <input
                            type="number"
                            className="w-24 px-2 py-1 border rounded"
                            value={formData.zig_salary}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                zig_salary: e.target.value,
                              })
                            }
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col">
                        <span className="text-sm font-medium">
                          {formatUSD(employee.usd_salary || 0)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatZIG(employee.zig_salary || 0)}
                        </span>
                      </div>
                    )}
                  </td>

                  {/* Allowances */}
                  <td className="px-6 py-4">
                    {editMode === employee.employeeid ? (
                      <div className="space-y-2">
                        {/* Display existing allowances for editing */}
                        {formData.allowances.map((allowance) => (
                          // Key by allowance.id since now it's a specific type
                          <div key={allowance.id} className="flex items-center gap-2">
                            <span className="text-sm">
                              {allowance.name}: {formatUSD(allowance.amount)}
                            </span>
                            <button
                              onClick={() => removeItem("allowances", allowance.id)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                        {/* Dropdown for adding new allowances */}
                        <div className="flex gap-2 mt-2">
                          <select
                            className="flex-1 px-2 py-1 border rounded text-sm"
                            value={selectedAllowanceTypeId}
                            onChange={(e) => setSelectedAllowanceTypeId(e.target.value)}
                          >
                            <option value="">Select Allowance Type</option>
                            {availableAllowances.map((type) => (
                              <option key={type.id} value={type.id}>
                                {type.name} ({formatUSD(type.amount)})
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={addAllowance}
                            className="text-green-600 hover:text-green-800 p-1 rounded-full bg-green-100"
                            title="Add Allowance"
                          >
                            <Plus className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        {/* Display current allowances */}
                        {employee.allowances?.length > 0 ? (
                          employee.allowances.map((allowance) => (
                            <div key={allowance.id} className="text-sm">
                              {allowance.name}: {formatUSD(allowance.amount)}
                            </div>
                          ))
                        ) : (
                          <span className="text-sm text-gray-400">None</span>
                        )}
                      </div>
                    )}
                  </td>

                  {/* Deductions */}
                  <td className="px-6 py-4">
                    {editMode === employee.employeeid ? (
                      <div className="space-y-2">
                        {/* Display existing deductions for editing */}
                        {formData.deductions.map((deduction) => (
                          // Key by deduction.id since now it's a specific type
                          <div key={deduction.id} className="flex items-center gap-2">
                            <span className="text-sm">
                              {deduction.name}: {formatUSD(deduction.amount)}
                            </span>
                            <button
                              onClick={() => removeItem("deductions", deduction.id)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                        {/* Dropdown for adding new deductions */}
                        <div className="flex gap-2 mt-2">
                          <select
                            className="flex-1 px-2 py-1 border rounded text-sm"
                            value={selectedDeductionTypeId}
                            onChange={(e) => setSelectedDeductionTypeId(e.target.value)}
                          >
                            <option value="">Select Deduction Type</option>
                            {availableDeductions.map((type) => (
                              <option key={type.id} value={type.id}>
                                {type.name} ({formatUSD(type.amount)})
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={addDeduction}
                            className="text-green-600 hover:text-green-800 p-1 rounded-full bg-green-100"
                            title="Add Deduction"
                          >
                            <Plus className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        {/* Display current deductions */}
                        {employee.deductions?.length > 0 ? (
                          employee.deductions.map((deduction) => (
                            <div key={deduction.id} className="text-sm">
                              {deduction.name}: {formatUSD(deduction.amount)}
                            </div>
                          ))
                        ) : (
                          <span className="text-sm text-gray-400">None</span>
                        )}
                      </div>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {editMode === employee.employeeid ? (
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleSave(employee.employeeid)}
                          disabled={loading}
                          className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50"
                        >
                          {loading ? (
                            <Loader className="h-4 w-4 animate-spin" />
                          ) : (
                            <Check className="h-4 w-4" />
                          )}
                          Save
                        </button>
                        <button
                          onClick={handleCancel}
                          className="flex items-center gap-1 px-3 py-1 bg-gray-200 text-gray-800 rounded text-sm hover:bg-gray-300"
                        >
                          <X className="h-4 w-4" />
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleEdit(employee)}
                        className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                      >
                        <Edit2 className="h-4 w-4" />
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="px-6 py-8 text-center">
                  <div className="flex flex-col items-center justify-center">
                    <DollarSign className="h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">
                      No employees found
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {searchTerm
                        ? "Try adjusting your search"
                        : "Add employees to get started"}
                    </p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SalarySetup;