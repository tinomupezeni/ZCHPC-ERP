import React, { useState, useEffect } from "react";
import {
  Calendar,
  Download,
  DollarSign,
  Search,
  ChevronDown,
  Printer,
  Mail,
  MoreVertical,
  Loader,
  Eye,
  Trash2,
  PlayCircle
} from "lucide-react";
import { format } from "date-fns";
import PayslipModal from "./PayslipModal";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { formatUSD, formatZIG } from "../ui/utils";
import { toast } from "sonner";

// Import your new specific services
import { 
  getPayslips, 
  deletePayslip, 
  approvePayslip, 
  processPayroll,
  PayrollRecord 
} from "@/services/payroll.services";
import { getDepartment } from "@/services/hr.services";

const PayrollDashboard = () => {
  // State
  const [selectedMonth, setSelectedMonth] = useState(new Date());
  const [showPayslip, setShowPayslip] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<PayrollRecord | null>(null);
  
  // Data State
  const [payrollRecords, setPayrollRecords] = useState<PayrollRecord[]>([]);
  const [departments, setDepartments] = useState<string[]>(["All Departments"]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("All Departments");
  const [selectedStatus, setSelectedStatus] = useState("All Statuses");
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  
  const [openMenuId, setOpenMenuId] = useState<number | null>(null);

  // --- 1. Initial Data Load ---
  useEffect(() => {
    loadData();
  }, [selectedMonth]);

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const period = format(selectedMonth, "yyyy-MM");
      const data = await getPayslips(period);
      console.log(data);
      
      setPayrollRecords(data);
    } catch (error) {
      console.error("Error fetching payroll:", error);
      toast.error("Failed to load payroll records");
    } finally {
      setLoading(false);
    }
  };

  const loadDepartments = async () => {
    try {
      // Reusing the HR service we created earlier
      const response = await getDepartment();
      // getDepartment may return axios response or array directly
      const depts = Array.isArray(response) ? response : response.data || [];
      // Extract just the names for the filter dropdown
      const deptNames = depts.map((d: any) => d.name);
      setDepartments(["All Departments", ...deptNames]);
    } catch (error) {
      console.error("Error fetching departments:", error);
    }
  };

  // --- 2. Actions ---

  const handleProcessPayroll = async () => {
    setProcessing(true);
    try {
      const period = format(selectedMonth, "yyyy-MM");
      const result = await processPayroll({ month: period });

      console.log("Payroll processing result:", result);

      // Show detailed feedback based on result
      const details = result.details || result;
      const processed = details.total_processed || 0;
      const skipped = details.total_skipped || 0;
      const errors = details.total_errors || 0;

      if (processed > 0) {
        toast.success(`Payroll processed: ${processed} employees`);
      }
      if (skipped > 0) {
        toast.info(`${skipped} employees skipped (already processed for this period)`);
      }
      if (errors > 0) {
        // Log full error details
        console.error("Payroll errors details:");
        details.errors?.forEach((err: any, i: number) => {
          console.error(`  ${i + 1}. Employee ${err.employee_id}: ${err.error}`);
        });
        // Show first error in toast
        const firstError = details.errors?.[0];
        toast.error(`${errors} errors: ${firstError?.error || 'Check console'}`);
      }
      if (processed === 0 && skipped === 0 && errors === 0) {
        toast.warning("No active employees found to process");
      }

      loadData(); // Refresh list
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.error || "Failed to process payroll");
    } finally {
      setProcessing(false);
    }
  };

  const handleDelete = async (id: number) => {
    if(!confirm("Are you sure? This will remove the payslip record.")) return;
    try {
      await deletePayslip(id);
      toast.success("Payslip deleted");
      // Optimistic update
      setPayrollRecords(prev => prev.filter(r => r.id !== id));
    } catch (error) {
      toast.error("Failed to delete payslip");
    }
  };

  const handleApprove = async (record: PayrollRecord) => {
    try {
      await approvePayslip(record.id);
      toast.success(`Approved ${record.employee_name}`);
      // Optimistic update
      setPayrollRecords(prev =>
        prev.map(r => r.id === record.id ? { ...r, status: "Processed" } : r)
      );
    } catch (error) {
      toast.error("Failed to approve");
    }
  };

  const exportToCSV = () => {
    if (payrollRecords.length === 0) {
        toast.warning("No records to export");
        return;
    }
    
    const headers = [
      "Employee ID", "Name", "Department", "Base USD", "Base ZiG", "Net USD", "Net ZiG", "Status"
    ];
    
    const csvRows = filteredRecords.map(r => 
      `"${r.employee_id}","${r.employee_name} ${r.employee_surname}","${r.employee_department}",` +
      `"${r.base_salary_usd}","${r.base_salary_zig}","${r.net_salary_usd}","${r.net_salary_zig}","${r.status}"`
    );

    const csvContent = [headers.join(","), ...csvRows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `payroll_${format(selectedMonth, "yyyy_MM")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // --- 3. Filtering & Pagination ---

  const filteredRecords = payrollRecords.filter((record) => {
    const matchesSearch = 
        record.employee_name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
        record.employee_surname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        record.employee_id?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDepartment = selectedDepartment === "All Departments" || record.employee_department === selectedDepartment;
    const matchesStatus = selectedStatus === "All Statuses" || record.status === selectedStatus;

    return matchesSearch && matchesDepartment && matchesStatus;
  });

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredRecords.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredRecords.length / itemsPerPage);

  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      "Processed": "bg-green-100 text-green-800",
      "Pending": "bg-yellow-100 text-yellow-800",
      "Failed": "bg-red-100 text-red-800",
      "Draft": "bg-gray-100 text-gray-800"
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles["Draft"]}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Payroll Dashboard</h1>
          <p className="text-sm text-gray-500">
            {payrollRecords.length} records for {format(selectedMonth, "MMMM yyyy")}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <Download className="h-4 w-4" /> Export
          </button>
          <button
            onClick={handleProcessPayroll}
            disabled={processing || loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition-colors disabled:opacity-70 shadow-sm"
          >
            {processing ? <Loader className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-5 w-5" />}
            Run Payroll
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="p-4 border-b flex flex-col md:flex-row gap-4">
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="month"
              className="pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              value={format(selectedMonth, "yyyy-MM")}
              onChange={(e) => {
                if(e.target.value) setSelectedMonth(new Date(e.target.value));
                setCurrentPage(1);
              }}
            />
          </div>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Search employee..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
          <div className="flex gap-2">
            <select
              className="border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
              value={selectedDepartment}
              onChange={(e) => { setSelectedDepartment(e.target.value); setCurrentPage(1); }}
            >
              {departments.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
            <select
              className="border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
              value={selectedStatus}
              onChange={(e) => { setSelectedStatus(e.target.value); setCurrentPage(1); }}
            >
              <option>All Statuses</option>
              <option>Processed</option>
              <option>Pending</option>
              <option>Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {["Employee", "Department", "Base (USD)", "Base (ZiG)", "Net (USD)", "Net (ZiG)", "Status", ""].map((h, i) => (
                    <th key={i} className={`px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider ${i > 1 && i < 6 ? 'text-right' : 'text-left'}`}>
                        {h}
                    </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={8} className="px-6 py-8 text-center text-gray-500"><Loader className="h-8 w-8 animate-spin mx-auto mb-2"/>Loading...</td></tr>
              ) : currentItems.length > 0 ? (
                currentItems.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                          {record.employee_name?.[0]}{record.employee_surname?.[0]}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{record.employee_name} </div>
                          <div className="text-sm text-gray-500">{record.employee_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{record.employee_department}</td>
                    <td className="px-6 py-4 text-sm text-right font-medium">{formatUSD(record.base_salary_usd)}</td>
                    <td className="px-6 py-4 text-sm text-right font-medium">{formatZIG(record.base_salary_zig)}</td>
                    <td className="px-6 py-4 text-sm text-right text-green-600 font-bold">{formatUSD(record.net_salary_usd)}</td>
                    <td className="px-6 py-4 text-sm text-right text-green-600 font-bold">{formatZIG(record.net_salary_zig)}</td>
                    <td className="px-6 py-4">{getStatusBadge(record.status)}</td>
                    <td className="px-6 py-4 text-right">
                      <Menu as="div" className="relative inline-block text-left">
                        <MenuButton className="p-2 hover:bg-gray-100 rounded-full" onClick={() => setOpenMenuId(openMenuId === record.id ? null : record.id)}>
                          <MoreVertical className="h-5 w-5 text-gray-400" />
                        </MenuButton>
                        <MenuItems className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                           <div className="py-1">
                             {record.status !== "Processed" && (
                               <MenuItem>
                                 {({ active }) => (
                                   <button onClick={() => handleApprove(record)} className={`${active ? "bg-green-50 text-green-700" : "text-gray-700"} flex w-full items-center px-4 py-2 text-sm`}>
                                     <DollarSign className="mr-2 h-4 w-4" /> Approve
                                   </button>
                                 )}
                               </MenuItem>
                             )}
                             <MenuItem>
                               {({ active }) => (
                                 <button onClick={() => { setSelectedRecord(record); setShowPayslip(true); }} className={`${active ? "bg-blue-50 text-blue-700" : "text-gray-700"} flex w-full items-center px-4 py-2 text-sm`}>
                                   <Eye className="mr-2 h-4 w-4" /> View Payslip
                                 </button>
                               )}
                             </MenuItem>
                             <MenuItem>
                               {({ active }) => (
                                 <button onClick={() => handleDelete(record.id)} className={`${active ? "bg-red-50 text-red-700" : "text-gray-700"} flex w-full items-center px-4 py-2 text-sm`}>
                                   <Trash2 className="mr-2 h-4 w-4" /> Delete
                                 </button>
                               )}
                             </MenuItem>
                           </div>
                        </MenuItems>
                      </Menu>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center">
                      <DollarSign className="h-12 w-12 text-gray-300 mb-3" />
                      <h3 className="text-lg font-medium text-gray-900">No payroll records</h3>
                      <p className="text-gray-500">Run payroll or adjust filters.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Component */}
        {filteredRecords.length > itemsPerPage && (
            <div className="px-6 py-4 border-t flex items-center justify-between bg-gray-50">
                <span className="text-sm text-gray-700">
                    Page {currentPage} of {totalPages}
                </span>
                <div className="flex gap-2">
                    <button 
                        onClick={() => paginate(currentPage - 1)} disabled={currentPage === 1}
                        className="px-3 py-1 border rounded bg-white disabled:opacity-50"
                    >
                        Prev
                    </button>
                    <button 
                        onClick={() => paginate(currentPage + 1)} disabled={currentPage === totalPages}
                        className="px-3 py-1 border rounded bg-white disabled:opacity-50"
                    >
                        Next
                    </button>
                </div>
            </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
         <div className="bg-white p-6 rounded-xl shadow-sm border border-blue-100">
            <p className="text-sm text-blue-600 font-medium">Total Gross (USD)</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">
                {formatUSD(payrollRecords.reduce((sum, r) => sum + (Number(r.base_salary_usd) || 0), 0))}
            </p>
         </div>
         <div className="bg-white p-6 rounded-xl shadow-sm border border-green-100">
            <p className="text-sm text-green-600 font-medium">Total Gross (ZiG)</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">
                {formatZIG(payrollRecords.reduce((sum, r) => sum + (Number(r.base_salary_zig) || 0), 0))}
            </p>
         </div>
         <div className="bg-white p-6 rounded-xl shadow-sm border border-yellow-100">
            <p className="text-sm text-yellow-600 font-medium">Processed Status</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">
                {payrollRecords.filter(r => r.status === 'Processed').length} / {payrollRecords.length}
            </p>
         </div>
      </div>

      {/* Payslip Modal */}
      {showPayslip && selectedRecord && (
        <PayslipModal
          PayrollRecord={selectedRecord}
          setShowPayslip={() => setShowPayslip(false)}
        />
      )}
    </div>
  );
};

export default PayrollDashboard;