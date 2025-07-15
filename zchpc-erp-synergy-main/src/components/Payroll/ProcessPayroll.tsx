import React, { useState, useEffect } from "react";
import {
  DollarSign,
  Calendar,
  CheckCircle,
  AlertCircle,
  Loader,
  ChevronDown,
  Download,
  Printer,
  Mail,
  Search,
  Clock,
} from "lucide-react";
import Server from "@/server/Server";
import { format, addMonths, subMonths } from "date-fns";
import { formatUSD, formatZIG } from "../ui/utils";
import { toast } from "sonner";
import PayrollSummaryCard from '../Payroll/PayrollSummaryCard'
import PayrollStatusBadge from "../Payroll/PayrollStatusBadge";

const ProcessPayroll = () => {
  const [selectedMonth, setSelectedMonth] = useState(new Date());
  const [payrollRun, setPayrollRun] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("All Departments");
  const [departments, setDepartments] = useState(["All Departments"]);

  // Fetch payroll data when month changes
  useEffect(() => {
    fetchPayrollData();
    fetchDepartments();
  }, [selectedMonth]);

  const fetchPayrollData = async () => {
    setLoading(true);
    try {
      const monthString = format(selectedMonth, "yyyy-MM");
      const [runResponse, employeesResponse] = await Promise.all([
        Server.getPayrollRun(monthString),
        Server.getEmployeesForPayroll(monthString),
      ]);

      setPayrollRun(runResponse.data);
      setEmployees(employeesResponse.data);
    } catch (error) {
      toast.error("Failed to fetch payroll data");
      console.error(error);
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

  const handleProcessPayroll = async () => {
    if (!confirm("Are you sure you want to process payroll for this month?")) {
      return;
    }

    setProcessing(true);
    try {
      const response = await Server.processPayroll({
        month: format(selectedMonth, "yyyy-MM"),
      });
      setPayrollRun(response.data);
      toast.success("Payroll processed successfully");
      fetchPayrollData(); // Refresh data
    } catch (error) {
      toast.error("Failed to process payroll");
      console.error(error);
    } finally {
      setProcessing(false);
    }
  };

  const handleApprovePayroll = async () => {
    if (!confirm("Approve this payroll run? This will make payments irreversible.")) {
      return;
    }

    try {
      await Server.approvePayroll(payrollRun.id);
      toast.success("Payroll approved successfully");
      fetchPayrollData(); // Refresh data
    } catch (error) {
      toast.error("Failed to approve payroll");
      console.error(error);
    }
  };

  const handleExportBankFile = async () => {
    try {
      const response = await Server.exportBankFile(payrollRun.id);
      // Create download link
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `payroll_${format(selectedMonth, "yyyy_MM")}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success("Bank file exported successfully");
    } catch (error) {
      toast.error("Failed to export bank file");
      console.error(error);
    }
  };

  const filteredEmployees = employees.filter((employee) => {
    const matchesSearch =
      employee.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.employeeId.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDepartment =
      selectedDepartment === "All Departments" ||
      employee.department === selectedDepartment;

    return matchesSearch && matchesDepartment;
  });

  // Calculate summary totals
  const summary = {
    totalGross: employees.reduce((sum, emp) => sum + (emp.grossSalary || 0), 0),
    totalDeductions: employees.reduce(
      (sum, emp) => sum + (emp.totalDeductions || 0),
      0
    ),
    totalNet: employees.reduce((sum, emp) => sum + (emp.netSalary || 0), 0),
    totalEmployees: employees.length,
    processedEmployees: employees.filter((emp) => emp.status === "Processed").length,
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Process Payroll</h1>
          <p className="text-sm text-gray-500">
            Run and manage monthly payroll processing
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSelectedMonth(subMonths(selectedMonth, 1))}
            className="p-2 rounded-lg border border-gray-300 hover:bg-gray-100"
          >
            &larr;
          </button>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="month"
              className="pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={format(selectedMonth, "yyyy-MM")}
              onChange={(e) => setSelectedMonth(new Date(e.target.value))}
            />
          </div>
          <button
            onClick={() => setSelectedMonth(addMonths(selectedMonth, 1))}
            className="p-2 rounded-lg border border-gray-300 hover:bg-gray-100"
            disabled={format(selectedMonth, "yyyy-MM") >= format(new Date(), "yyyy-MM")}
          >
            &rarr;
          </button>
        </div>
      </div>

      {/* Payroll Status Banner */}
      {payrollRun && (
        <div
          className={`p-4 rounded-lg mb-6 ${
            payrollRun.status === "Processed"
              ? "bg-green-50 border border-green-200"
              : payrollRun.status === "Pending"
              ? "bg-yellow-50 border border-yellow-200"
              : "bg-red-50 border border-red-200"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {payrollRun.status === "Processed" ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : payrollRun.status === "Pending" ? (
                <Clock className="h-5 w-5 text-yellow-600" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600" />
              )}
              <div>
                <h3 className="font-medium">
                  Payroll for {format(selectedMonth, "MMMM yyyy")} is{" "}
                  <span
                    className={
                      payrollRun.status === "Processed"
                        ? "text-green-700"
                        : payrollRun.status === "Pending"
                        ? "text-yellow-700"
                        : "text-red-700"
                    }
                  >
                    {payrollRun.status}
                  </span>
                </h3>
                <p className="text-sm text-gray-600">
                  {payrollRun.processedAt
                    ? `Processed on ${format(new Date(payrollRun.processedAt), "PPP")}`
                    : "Not yet processed"}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              {payrollRun.status === "Processed" && (
                <>
                  <button
                    onClick={handleExportBankFile}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                  >
                    <Download className="h-4 w-4" />
                    Export Bank File
                  </button>
                  <button
                    onClick={handleApprovePayroll}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    <CheckCircle className="h-4 w-4" />
                    Approve Payroll
                  </button>
                </>
              )}
              {(!payrollRun || payrollRun.status === "Draft") && (
                <button
                  onClick={handleProcessPayroll}
                  disabled={processing}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-70"
                >
                  {processing ? (
                    <Loader className="h-4 w-4 animate-spin" />
                  ) : (
                    <DollarSign className="h-4 w-4" />
                  )}
                  Process Payroll
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <PayrollSummaryCard
          title="Total Gross Pay"
          value={formatUSD(summary.totalGross)}
          secondaryValue={formatZIG(summary.totalGross * 12)} // Assuming 1:12 USD:ZIG rate
          icon={<DollarSign className="h-5 w-5 text-blue-600" />}
          color="blue"
        />
        <PayrollSummaryCard
          title="Total Deductions"
          value={formatUSD(summary.totalDeductions)}
          secondaryValue={formatZIG(summary.totalDeductions * 12)}
          icon={<DollarSign className="h-5 w-5 text-red-600" />}
          color="red"
        />
        <PayrollSummaryCard
          title="Total Net Pay"
          value={formatUSD(summary.totalNet)}
          secondaryValue={formatZIG(summary.totalNet * 12)}
          icon={<DollarSign className="h-5 w-5 text-green-600" />}
          color="green"
        />
        <PayrollSummaryCard
          title="Employees"
          value={`${summary.processedEmployees}/${summary.totalEmployees}`}
          subtitle="Processed/Total"
          icon={<DollarSign className="h-5 w-5 text-purple-600" />}
          color="purple"
        />
      </div>

      {/* Filters */}
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
          <div className="relative w-full md:w-64">
            <select
              className="appearance-none w-full border rounded-lg px-4 py-2 pr-8 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
            >
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Payroll Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Employee
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Department
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Gross Salary
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Deductions
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Net Salary
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan="7" className="px-6 py-8 text-center">
                  <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                  <p className="mt-2 text-sm text-gray-500">
                    Loading payroll data...
                  </p>
                </td>
              </tr>
            ) : filteredEmployees.length > 0 ? (
              filteredEmployees.map((employee) => (
                <tr key={employee.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                        {employee.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {employee.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {employee.employeeId}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {employee.department}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex flex-col">
                      <span>{formatUSD(employee.grossSalary)}</span>
                      <span className="text-xs text-gray-500">
                        {formatZIG(employee.grossSalary * 12)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-red-600">
                    {formatUSD(employee.totalDeductions)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-green-600">
                    <div className="flex flex-col">
                      <span>{formatUSD(employee.netSalary)}</span>
                      <span className="text-xs text-gray-500">
                        {formatZIG(employee.netSalary * 12)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <PayrollStatusBadge status={employee.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <button className="p-1 text-blue-600 hover:text-blue-800">
                        <Printer className="h-5 w-5" />
                      </button>
                      <button className="p-1 text-blue-600 hover:text-blue-800">
                        <Mail className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" className="px-6 py-8 text-center">
                  <div className="flex flex-col items-center justify-center">
                    <DollarSign className="h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">
                      No payroll records found
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {searchTerm
                        ? "Try adjusting your search or filter"
                        : "Process payroll for the selected month to get started"}
                    </p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Statutory Reports Section */}
      {payrollRun && payrollRun.status === "Processed" && (
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-800 mb-4">
            Statutory Reports
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => toast.success("PAYE report generated")}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
            >
              <div className="font-medium text-blue-600">PAYE Return</div>
              <p className="text-sm text-gray-500 mt-1">
                Zimbabwe Revenue Authority report
              </p>
            </button>
            <button
              onClick={() => toast.success("NSSA report generated")}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
            >
              <div className="font-medium text-blue-600">NSSA Return</div>
              <p className="text-sm text-gray-500 mt-1">
                Pension contributions report
              </p>
            </button>
            <button
              onClick={() => toast.success("ZIMDEF report generated")}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
            >
              <div className="font-medium text-blue-600">ZIMDEF Return</div>
              <p className="text-sm text-gray-500 mt-1">
                Skills development levy report
              </p>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProcessPayroll;