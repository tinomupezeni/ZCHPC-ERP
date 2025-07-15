import React, { useState, useEffect } from "react";
import { Calendar, Download, DollarSign, Search, Filter, ChevronDown, Printer, Mail, MoreVertical, Loader } from "lucide-react";
import { format } from "date-fns";
import PayslipModal from "./PayslipModal";
import { Menu, MenuButton, MenuItem, MenuList } from "@headlessui/react";
import Server from "@/server/Server";

const PayrollDashboard = () => {
  const [selectedMonth, setSelectedMonth] = useState(new Date());
  const [showPayslip, setShowPayslip] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [payrollRecords, setPayrollRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [selectedStatus, setSelectedStatus] = useState("All Statuses");
  const [departments, setDepartments] = useState(["All Departments"]);
  const [selectedDepartment, setSelectedDepartment] = useState("All Departments");

  useEffect(() => {
    fetchPayrollRecords();
    fetchDepartments();
  }, [selectedMonth]);

  const fetchPayrollRecords = async () => {
    setLoading(true);
    try {
      const response = await Server.fetchPayrollRecords({
        month: format(selectedMonth, "yyyy-MM")
      });
      console.log(response.data);
      
      setPayrollRecords(response.data);
    } catch (error) {
      console.error("Error fetching payroll records:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await Server.fetchDepartments();
      setDepartments(["All Departments", ...response.data]);
    } catch (error) {
      console.error("Error fetching departments:", error);
    }
  };

  const filteredRecords = payrollRecords.filter(record => {
    const matchesSearch = 
      record.employee.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.employee.employeeId.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesDepartment = 
      selectedDepartment === "All Departments" || 
      record.employee.department === selectedDepartment;
    
    const matchesStatus = 
      selectedStatus === "All Statuses" || 
      record.status === selectedStatus;
    
    return matchesSearch && matchesDepartment && matchesStatus;
  });

  // Pagination logic
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredRecords.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredRecords.length / itemsPerPage);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  const processPayroll = async () => {
    setLoading(true);
    try {
      await Server.processPayroll({
        month: format(selectedMonth, "yyyy-MM")
      });
      toast.success("Payroll processed successfully");
      fetchPayrollRecords();
    } catch (error) {
      console.error("Error processing payroll:", error);
      toast.error("Error processing payroll");
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    const headers = ["Employee ID", "Name", "Department", "Base Salary (USD)", "Base Salary (ZIG)", "Net Salary (USD)", "Net Salary (ZIG)", "Status"];
    const csvContent = [
      headers.join(","),
      ...filteredRecords.map(record => 
        `"${record.employee.employeeId}","${record.employee.name}","${record.employee.department}","${record.salary.baseSalaryUSD.toFixed(2)}","${record.salary.baseSalaryZIG.toFixed(2)}","${record.salary.netSalaryUSD.toFixed(2)}","${record.salary.netSalaryZIG.toFixed(2)}","${record.status}"`
      )
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `payroll_${format(selectedMonth, "yyyy_MM")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getStatusBadge = (status) => {
    switch(status) {
      case "Processed":
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Processed</span>;
      case "Pending":
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">Pending</span>;
      case "Failed":
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">Failed</span>;
      default:
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Payroll Management</h1>
          <p className="text-sm text-gray-500">
            {filteredRecords.length} {filteredRecords.length === 1 ? "record" : "records"} for {format(selectedMonth, "MMMM yyyy")}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            onClick={processPayroll}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition-colors disabled:opacity-70"
          >
            {loading && <Loader className="h-4 w-4 animate-spin" />}
            <DollarSign className="h-5 w-5" />
            Process Payroll
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="p-4 border-b">
          <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="month"
                className="pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={format(selectedMonth, "yyyy-MM")}
                onChange={(e) => {
                  setSelectedMonth(new Date(e.target.value));
                  setCurrentPage(1);
                }}
              />
            </div>
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                placeholder="Search by name or employee ID..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
            <div className="flex flex-wrap gap-2 w-full md:w-auto">
              <div className="relative">
                <select 
                  className="appearance-none border rounded-lg px-4 py-2 pr-8 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={selectedDepartment}
                  onChange={(e) => {
                    setSelectedDepartment(e.target.value);
                    setCurrentPage(1);
                  }}
                >
                  {departments.map((dept) => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              </div>
              <div className="relative">
                <select 
                  className="appearance-none border rounded-lg px-4 py-2 pr-8 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={selectedStatus}
                  onChange={(e) => {
                    setSelectedStatus(e.target.value);
                    setCurrentPage(1);
                  }}
                >
                  <option>All Statuses</option>
                  <option>Processed</option>
                  <option>Pending</option>
                  <option>Failed</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Department
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Base Salary (USD)
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Base Salary (ZIG)
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Net Salary (USD)
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Net Salary (ZIG)
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-6 py-8 text-center">
                    <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                    <p className="mt-2 text-sm text-gray-500">Loading payroll records...</p>
                  </td>
                </tr>
              ) : currentItems.length > 0 ? (
                currentItems.map((record) => (
                  <tr key={`${record.employee.employeeId}-${record.period}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                          {record.employee.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {record.employee.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {record.employee.employeeId}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record.employee.department}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      ${record.salary.baseSalaryUSD.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {record.salary.baseSalaryZIG.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      ${record.salary.netSalaryUSD.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {record.salary.netSalaryZIG.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(record.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Menu as="div" className="relative inline-block text-left">
                        <div>
                          <MenuButton className="inline-flex justify-center w-full rounded-md px-2 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 focus:outline-none">
                            <MoreVertical className="h-5 w-5 text-gray-400" />
                          </MenuButton>
                        </div>
                        <MenuList className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                          <MenuItem>
                            {({ active }) => (
                              <button
                                onClick={() => {
                                  setSelectedRecord(record);
                                  setShowPayslip(true);
                                }}
                                className={`${
                                  active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                } group flex items-center w-full px-4 py-2 text-sm`}
                              >
                                View Payslip
                              </button>
                            )}
                          </MenuItem>
                          <MenuItem>
                            {({ active }) => (
                              <button
                                className={`${
                                  active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                } group flex items-center w-full px-4 py-2 text-sm`}
                              >
                                <Printer className="mr-2 h-4 w-4" />
                                Print Payslip
                              </button>
                            )}
                          </MenuItem>
                          <MenuItem>
                            {({ active }) => (
                              <button
                                className={`${
                                  active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                } group flex items-center w-full px-4 py-2 text-sm`}
                              >
                                <Mail className="mr-2 h-4 w-4" />
                                Email Payslip
                              </button>
                            )}
                          </MenuItem>
                          {record.status === "Failed" && (
                            <MenuItem>
                              {({ active }) => (
                                <button
                                  className={`${
                                    active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                  } group flex items-center w-full px-4 py-2 text-sm`}
                                >
                                  Retry Payment
                                </button>
                              )}
                            </MenuItem>
                          )}
                        </MenuList>
                      </Menu>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="px-6 py-8 text-center">
                    <div className="flex flex-col items-center justify-center">
                      <DollarSign className="h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No payroll records found</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {searchTerm ? "Try adjusting your search or filter" : "Process payroll for the selected month to get started"}
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {filteredRecords.length > itemsPerPage && (
          <div className="px-6 py-4 border-t flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing <span className="font-medium">{indexOfFirstItem + 1}</span> to{" "}
              <span className="font-medium">
                {Math.min(indexOfLastItem, filteredRecords.length)}
              </span>{" "}
              of <span className="font-medium">{filteredRecords.length}</span> results
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => paginate(currentPage - 1)}
                disabled={currentPage === 1}
                className={`px-3 py-1 rounded-md border ${currentPage === 1 ? "bg-gray-100 text-gray-400 cursor-not-allowed" : "hover:bg-gray-100"}`}
              >
                Previous
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((number) => (
                <button
                  key={number}
                  onClick={() => paginate(number)}
                  className={`px-3 py-1 rounded-md border ${currentPage === number ? "bg-blue-600 text-white" : "hover:bg-gray-100"}`}
                >
                  {number}
                </button>
              ))}
              <button
                onClick={() => paginate(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={`px-3 py-1 rounded-md border ${currentPage === totalPages ? "bg-gray-100 text-gray-400 cursor-not-allowed" : "hover:bg-gray-100"}`}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Payroll Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
        <h2 className="text-lg font-medium text-gray-800 mb-4">Payroll Summary - {format(selectedMonth, "MMMM yyyy")}</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <div className="text-sm font-medium text-blue-800">Total Payroll (USD)</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">
              ${filteredRecords.reduce((sum, record) => sum + record.salary.netSalaryUSD, 0).toFixed(2)}
            </div>
            <div className="text-xs text-blue-500 mt-2">Net amount</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-100">
            <div className="text-sm font-medium text-green-800">Total Payroll (ZIG)</div>
            <div className="text-2xl font-bold text-green-600 mt-1">
              {filteredRecords.reduce((sum, record) => sum + record.salary.netSalaryZIG, 0).toFixed(2)}
            </div>
            <div className="text-xs text-green-500 mt-2">Net amount</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
            <div className="text-sm font-medium text-purple-800">Total Deductions</div>
            <div className="text-2xl font-bold text-purple-600 mt-1">
              ${filteredRecords.reduce((sum, record) => sum + (record.salary.baseSalaryUSD - record.salary.netSalaryUSD), 0).toFixed(2)}
            </div>
            <div className="text-xs text-purple-500 mt-2">Taxes & Contributions</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100">
            <div className="text-sm font-medium text-yellow-800">Employees Paid</div>
            <div className="text-2xl font-bold text-yellow-600 mt-1">
              {filteredRecords.filter(r => r.status === "Processed").length}/{filteredRecords.length}
            </div>
            <div className="text-xs text-yellow-500 mt-2">Successfully processed</div>
          </div>
        </div>
      </div>

      {showPayslip && selectedRecord && (
        <PayslipModal
          PayrollRecord={selectedRecord}
          setShowPayslip={setShowPayslip}
        />
      )}
    </div>
  );
};

export default PayrollDashboard;