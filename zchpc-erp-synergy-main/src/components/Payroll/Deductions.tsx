import React, { useState, useEffect } from "react";
import {
  DollarSign,
  Search,
  ChevronDown,
  Trash2,
  Edit2,
  Check,
  X,
  Loader,
  Plus,
  FileText,
  Shield,
  Heart,
} from "lucide-react";
import Server from "@/server/Server";
import { formatUSD, formatZIG } from "../ui/utils";
import { toast } from "sonner";

const Deductions = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [editMode, setEditMode] = useState(null);
  const [formData, setFormData] = useState({
    statutory: [],
    voluntary: [],
  });
  const [newDeduction, setNewDeduction] = useState({
    type: "voluntary",
    name: "",
    amount: "",
    fixedAmount: true,
  });
  const [activeTab, setActiveTab] = useState("statutory");

  // Statutory deduction templates (Zimbabwe-specific)
  const statutoryTemplates = [
    { name: "PAYE", description: "Pay As You Earn Tax", fixedAmount: false },
    { name: "NSSA", description: "Pension Contribution", fixedAmount: true, amount: 60 },
    { name: "AIDS Levy", description: "1% of gross salary", fixedAmount: false },
    { name: "ZIMDEF", description: "Skills Development Levy", fixedAmount: true, amount: 50 },
  ];

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await Server.fetchEmployees();
      setEmployees(response.data);
    } catch (error) {
      toast.error("Failed to fetch employee deductions");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const filteredEmployees = employees.filter((emp) =>
    emp.firstname.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.employeeid.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleEdit = (employee) => {
    setEditMode(employee.employeeid);
    setFormData({
      statutory: employee.deductions?.statutory || [],
      voluntary: employee.deductions?.voluntary || [],
    });
  };

  const handleCancel = () => {
    setEditMode(null);
    setFormData({
      statutory: [],
      voluntary: [],
    });
  };

  const handleSave = async (employeeId) => {
    setLoading(true);
    try {
      await Server.updateEmployeeDeductions(employeeId, formData);
      toast.success("Deductions updated successfully");
      fetchEmployees();
      setEditMode(null);
    } catch (error) {
      toast.error("Failed to update deductions");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const addDeduction = () => {
    if (!newDeduction.name) {
      toast.error("Deduction name is required");
      return;
    }

    const deduction = {
      name: newDeduction.name,
      amount: newDeduction.amount || 0,
      fixedAmount: newDeduction.fixedAmount,
    };

    setFormData({
      ...formData,
      [newDeduction.type]: [...formData[newDeduction.type], deduction],
    });

    setNewDeduction({
      type: "voluntary",
      name: "",
      amount: "",
      fixedAmount: true,
    });
  };

  const removeDeduction = (type, index) => {
    const updatedDeductions = [...formData[type]];
    updatedDeductions.splice(index, 1);
    setFormData({ ...formData, [type]: updatedDeductions });
  };

  const addStatutoryTemplate = (template) => {
    // Check if this template already exists
    if (formData.statutory.some(d => d.name === template.name)) {
      toast.error("This deduction already exists");
      return;
    }

    setFormData({
      ...formData,
      statutory: [...formData.statutory, {
        name: template.name,
        description: template.description,
        amount: template.amount || 0,
        fixedAmount: template.fixedAmount,
        statutory: true
      }]
    });
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Deductions Management</h1>
          <p className="text-sm text-gray-500">
            Configure statutory and voluntary deductions for employees
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

      {/* Tabs */}
      <div className="flex border-b mb-6">
        <button
          className={`px-4 py-2 font-medium ${activeTab === "statutory" ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-500"}`}
          onClick={() => setActiveTab("statutory")}
        >
          Statutory Deductions
        </button>
        <button
          className={`px-4 py-2 font-medium ${activeTab === "voluntary" ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-500"}`}
          onClick={() => setActiveTab("voluntary")}
        >
          Voluntary Deductions
        </button>
      </div>

      {/* Employee Deductions Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Employee
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {activeTab === "statutory" ? "Statutory Deductions" : "Voluntary Deductions"}
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan="3" className="px-6 py-8 text-center">
                  <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                  <p className="mt-2 text-sm text-gray-500">
                    Loading employee deductions...
                  </p>
                </td>
              </tr>
            ) : filteredEmployees.length > 0 ? (
              filteredEmployees.map((employee) => (
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
                          {employee.firstname}  {employee.surname}
                        </div>
                        <div className="text-sm text-gray-500">
                          {employee.department} • {employee.employeeid}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    {editMode === employee.employeeid ? (
                      <div className="space-y-3">
                        {/* Statutory Deductions Editor */}
                        {activeTab === "statutory" && (
                          <>
                            <div className="flex flex-wrap gap-2 mb-3">
                              {statutoryTemplates.map((template, index) => (
                                <button
                                  key={index}
                                  onClick={() => addStatutoryTemplate(template)}
                                  className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs hover:bg-gray-200"
                                >
                                  <Plus className="h-3 w-3" />
                                  {template.name}
                                </button>
                              ))}
                            </div>

                            {formData.statutory.map((deduction, index) => (
                              <div key={index} className="flex items-center gap-3">
                                <div className="flex-1">
                                  <div className="text-sm font-medium">{deduction.name}</div>
                                  {deduction.description && (
                                    <div className="text-xs text-gray-500">{deduction.description}</div>
                                  )}
                                </div>
                                {deduction.fixedAmount ? (
                                  <div className="text-sm font-medium">
                                    {formatUSD(deduction.amount)}
                                  </div>
                                ) : (
                                  <input
                                    type="number"
                                    value={deduction.amount}
                                    onChange={(e) => {
                                      const updated = [...formData.statutory];
                                      updated[index].amount = e.target.value;
                                      setFormData({ ...formData, statutory: updated });
                                    }}
                                    className="w-20 px-2 py-1 border rounded text-sm"
                                    placeholder="Amount"
                                  />
                                )}
                                <button
                                  onClick={() => removeDeduction("statutory", index)}
                                  className="text-red-500 hover:text-red-700"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </div>
                            ))}
                          </>
                        )}

                        {/* Voluntary Deductions Editor */}
                        {activeTab === "voluntary" && (
                          <>
                            {formData.voluntary.map((deduction, index) => (
                              <div key={index} className="flex items-center gap-3">
                                <input
                                  type="text"
                                  value={deduction.name}
                                  onChange={(e) => {
                                    const updated = [...formData.voluntary];
                                    updated[index].name = e.target.value;
                                    setFormData({ ...formData, voluntary: updated });
                                  }}
                                  className="flex-1 px-2 py-1 border rounded text-sm"
                                  placeholder="Deduction name"
                                />
                                <input
                                  type="number"
                                  value={deduction.amount}
                                  onChange={(e) => {
                                    const updated = [...formData.voluntary];
                                    updated[index].amount = e.target.value;
                                    setFormData({ ...formData, voluntary: updated });
                                  }}
                                  className="w-20 px-2 py-1 border rounded text-sm"
                                  placeholder="Amount"
                                />
                                <div className="flex items-center gap-1 text-xs">
                                  <input
                                    type="checkbox"
                                    id={`fixed-${index}`}
                                    checked={deduction.fixedAmount}
                                    onChange={(e) => {
                                      const updated = [...formData.voluntary];
                                      updated[index].fixedAmount = e.target.checked;
                                      setFormData({ ...formData, voluntary: updated });
                                    }}
                                  />
                                  <label htmlFor={`fixed-${index}`}>Fixed</label>
                                </div>
                                <button
                                  onClick={() => removeDeduction("voluntary", index)}
                                  className="text-red-500 hover:text-red-700"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </div>
                            ))}

                            <div className="flex gap-2 mt-2">
                              <input
                                type="text"
                                placeholder="New deduction name"
                                className="flex-1 px-2 py-1 border rounded text-sm"
                                value={newDeduction.name}
                                onChange={(e) =>
                                  setNewDeduction({ ...newDeduction, name: e.target.value })
                                }
                              />
                              <input
                                type="number"
                                placeholder="Amount"
                                className="w-20 px-2 py-1 border rounded text-sm"
                                value={newDeduction.amount}
                                onChange={(e) =>
                                  setNewDeduction({ ...newDeduction, amount: e.target.value })
                                }
                              />
                              <button
                                onClick={addDeduction}
                                className="flex items-center gap-1 px-2 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                              >
                                <Plus className="h-4 w-4" />
                                Add
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {(activeTab === "statutory"
                          ? employee.deductions?.statutory
                          : employee.deductions?.voluntary
                        )?.length > 0 ? (
                          (activeTab === "statutory"
                            ? employee.deductions.statutory
                            : employee.deductions.voluntary
                          ).map((deduction, index) => (
                            <div key={index} className="flex items-baseline gap-2">
                              <div className="text-sm">
                                <span className="font-medium">{deduction.name}</span>:{" "}
                                {deduction.fixedAmount ? (
                                  <span>{formatUSD(deduction.amount)}</span>
                                ) : (
                                  <span>{deduction.amount}%</span>
                                )}
                              </div>
                              {deduction.statutory && (
                                <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded-full">
                                  Statutory
                                </span>
                              )}
                            </div>
                          ))
                        ) : (
                          <span className="text-sm text-gray-400">
                            No {activeTab === "statutory" ? "statutory" : "voluntary"} deductions
                          </span>
                        )}
                      </div>
                    )}
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {editMode === employee.employeeid ? (
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleSave(employee.id)}
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
                <td colSpan="3" className="px-6 py-8 text-center">
                  <div className="flex flex-col items-center justify-center">
                    <FileText className="h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">
                      No employees found
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {searchTerm
                        ? "Try adjusting your search"
                        : "Add employees to configure deductions"}
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

export default Deductions;