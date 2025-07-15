import Server from "@/server/Server";
import { Loader, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import TaxAndDeductionsDropdown from "./TaxAndDeductions";

export default function AddEmployee({ setShowModal, fetchEmployees }) {
  const [loading, setLoading] = useState(false);
  const [selectedDeductions, setSelectedDeductions] = useState([]);
  const [employee, setEmployee] = useState({
    firstname: "",
    surname: "",
    nationalId: "",
    dob: "",
    gender: "",
    maritalStatus: "",
    email: "",
    phone: "",
    bankName: "",
    accountNumber: "",
    payFrequency: "Monthly",
    employeeType: "Full-Time",
    leaveDays: 21,
    pensionScheme: "",
    position: "",
    department: "",
    usd_salary: "",
    zig_salary: "",
    contractFrom: "",
    contractTo: "",
    emergencyContactName: "",
    emergencyContactPhone: "",
    emergencyContactRelationship: "",
    selectedDeductions,
  });

  const handleChange = (e) => {
    setEmployee({ ...employee, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    console.log(employee);
    // setLoading(false);

    try {
      await Server.addEmployee(employee);
      toast.success("Employee added successfully");
      setShowModal(false);
      fetchEmployees();
    } catch (error) {
      console.error("Error adding employee:", error);
      toast.error("Error adding employee");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl w-full max-w-2xl shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-blue-600 p-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-white">Add New Employee</h2>
          <button
            onClick={() => setShowModal(false)}
            className="text-white hover:text-blue-200 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form - Using tabs for better organization */}
        <form
          onSubmit={handleSubmit}
          className="max-h-[70vh] overflow-y-auto p-6"
        >
          {/* Personal Information Section */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4 pb-2 border-b border-gray-200">
              Personal Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  First Name*
                </label>
                <input
                  type="text"
                  name="firstname"
                  value={employee.firstname}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Surname*
                </label>
                <input
                  type="text"
                  name="surname"
                  value={employee.surname}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  National ID/Passport*
                </label>
                <input
                  type="text"
                  name="nationalId"
                  value={employee.nationalId}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date of Birth*
                </label>
                <input
                  type="date"
                  name="dob"
                  value={employee.dob}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gender*
                </label>
                <select
                  name="gender"
                  value={employee.gender}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select Gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Marital Status
                </label>
                <select
                  name="maritalStatus"
                  value={employee.maritalStatus}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select Status</option>
                  <option value="Single">Single</option>
                  <option value="Married">Married</option>
                  <option value="Divorced">Divorced</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email*
                </label>
                <input
                  type="email"
                  name="email"
                  value={employee.email}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone*
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={employee.phone}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Employment Details Section */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4 pb-2 border-b border-gray-200">
              Employment Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Position*
                </label>
                <input
                  type="text"
                  name="position"
                  value={employee.position}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Department*
                </label>
                <input
                  type="text"
                  name="department"
                  value={employee.department}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employee Type*
                </label>
                <select
                  name="employeeType"
                  value={employee.employeeType}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="Full-Time">Full-Time</option>
                  <option value="Part-Time">Part-Time</option>
                  <option value="Contract">Contract</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Leave Days/Year
                </label>
                <input
                  type="number"
                  name="leaveDays"
                  value={employee.leaveDays}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contract Start*
                </label>
                <input
                  type="date"
                  name="contractFrom"
                  value={employee.contractFrom}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contract End*
                </label>
                <input
                  type="date"
                  name="contractTo"
                  value={employee.contractTo}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Salary & Banking Section */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4 pb-2 border-b border-gray-200">
              Salary & Banking
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Basic Salary (USD)*
                </label>
                <input
                  type="number"
                  name="usd_salary"
                  value={employee.usd_salary}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Basic Salary (ZiG)*
                </label>
                <input
                  type="number"
                  name="zig_salary"
                  value={employee.zig_salary}
                  onChange={handleChange}
                  required
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pay Frequency*
                </label>
                <select
                  name="payFrequency"
                  value={employee.payFrequency}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="Monthly">Monthly</option>
                  <option value="Bi-Weekly">Bi-Weekly</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bank Name
                </label>
                <input
                  type="text"
                  name="bankName"
                  value={employee.bankName}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account Number
                </label>
                <input
                  type="text"
                  name="accountNumber"
                  value={employee.accountNumber}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pension Scheme
                </label>
                <input
                  type="text"
                  name="pensionScheme"
                  value={employee.pensionScheme}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Tax & Statutory Information */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4 pb-2 border-b border-gray-200">
              Tax & Statutory Information
            </h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Taxes & Deductions
              </label>
              <TaxAndDeductionsDropdown onSelect={setSelectedDeductions} />
            </div>

            {/* Display selected items */}
            {selectedDeductions.length > 0 && (
              <div className="mt-2">
                <h4 className="text-sm font-medium text-gray-700">
                  Selected Deductions:
                </h4>
                <ul className="mt-1 space-y-1">
                  {selectedDeductions.map((item) => (
                    <li key={item.id} className="text-sm text-gray-600">
                      • {item.name}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Emergency Contact */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4 pb-2 border-b border-gray-200">
              Emergency Contact
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Name
                </label>
                <input
                  type="text"
                  name="emergencyContactName"
                  value={employee.emergencyContactName}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Phone
                </label>
                <input
                  type="tel"
                  name="emergencyContactPhone"
                  value={employee.emergencyContactPhone}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Relationship
                </label>
                <input
                  type="text"
                  name="emergencyContactRelationship"
                  value={employee.emergencyContactRelationship}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={() => setShowModal(false)}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-70"
            >
              {loading && <Loader className="h-4 w-4 animate-spin mr-2" />}
              {loading ? "Adding Employee..." : "Add Employee"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
