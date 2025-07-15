import { useState, useEffect } from "react";
import { Search, Mail, Download, X, Eye, Loader, Check, AlertCircle, ChevronDown } from "lucide-react";
import Server from "@/server/Server";
import { toast } from "sonner";
import PayslipTemplate from "./ProcessPayroll";
import { PDFDownloadLink, PDFViewer } from "@react-pdf/renderer";

const PayslipGeneration = () => {
  const [loading, setLoading] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [payslipData, setPayslipData] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedAction, setSelectedAction] = useState(null);

  var  payrollPeriod = 'april 2025'

  const onClose = () => {
    console.log('done');
    
  }

  // Fetch employees when component mounts
  useEffect(() => {
    fetchEmployees();
  }, []);

  // Fetch payslip data when employee is selected
  useEffect(() => {
    if (selectedEmployee) {
      fetchPayslipData();
    }
  }, [selectedEmployee]);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await Server.fetchEmployees();
      setEmployees(response.data);
    } catch (error) {
      console.error("Error fetching employees:", error);
      toast.error("Failed to load employees");
    } finally {
      setLoading(false);
    }
  };

  const fetchPayslipData = async () => {
    setLoading(true);
    try {
      const response = await Server.getPayslipData({
        employeeId: selectedEmployee.id,
        period: payrollPeriod
      });
      setPayslipData(response.data);
    } catch (error) {
      console.error("Error fetching payslip data:", error);
      toast.error("Failed to load payslip data");
    } finally {
      setLoading(false);
    }
  };

  const sendPayslipEmail = async () => {
    setLoading(true);
    try {
      await Server.sendPayslipEmail({
        employeeId: selectedEmployee.id,
        period: payrollPeriod
      });
      toast.success("Payslip emailed successfully");
      setEmailSent(true);
    } catch (error) {
      console.error("Error sending payslip email:", error);
      toast.error("Failed to send payslip email");
    } finally {
      setLoading(false);
    }
  };

  const handleAction = (action) => {
    setSelectedAction(action);
    switch(action) {
      case "preview":
        setPreviewMode(true);
        break;
      case "email":
        sendPayslipEmail();
        break;
      default:
        break;
    }
  };

  const filteredEmployees = employees.filter(employee => 
    employee.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    employee.employeeId?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (previewMode && selectedEmployee && payslipData) {
    return (
      <div className="fixed  flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl w-full max-w-4xl h-[90vh] flex flex-col">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="text-xl font-semibold">
              Payslip Preview - {selectedEmployee.name} - {payrollPeriod}
            </h2>
            <button 
              onClick={() => setPreviewMode(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <PDFViewer className="w-full h-full">
              <PayslipTemplate 
                employee={selectedEmployee} 
                payrollData={payslipData} 
                period={payrollPeriod}
              />
            </PDFViewer>
          </div>
          <div className="p-4 border-t flex justify-end gap-3">
            <PDFDownloadLink
              document={<PayslipTemplate employee={selectedEmployee} payrollData={payslipData} period={payrollPeriod} />}
              fileName={`Payslip_${selectedEmployee.name.replace(" ", "_")}_${payrollPeriod.replace(" ", "_")}.pdf`}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Download
            </PDFDownloadLink>
            <button
              onClick={() => {
                setPreviewMode(false);
                handleAction("email");
              }}
              disabled={emailSent}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${emailSent ? "bg-green-100 text-green-800" : "bg-blue-600 text-white hover:bg-blue-700"}`}
            >
              {emailSent ? (
                <>
                  <Check className="h-4 w-4" />
                  Email Sent
                </>
              ) : (
                <>
                  <Mail className="h-4 w-4" />
                  Email Payslip
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!selectedEmployee) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl w-full max-w-2xl">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="text-xl font-semibold">Select Employee</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="p-4">
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                placeholder="Search employees by name or ID..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {loading ? (
              <div className="flex justify-center py-8">
                <Loader className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : (
              <div className="max-h-[60vh] overflow-y-auto">
                {filteredEmployees.length > 0 ? (
                  <ul className="divide-y divide-gray-200">
                    {filteredEmployees.map((employee) => (
                      <li key={employee.id}>
                        <button
                          onClick={() => setSelectedEmployee(employee)}
                          className="w-full p-4 text-left hover:bg-gray-50 flex items-center gap-4"
                        >
                          <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                            {employee.name.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">{employee.name}</div>
                            <div className="text-sm text-gray-500">{employee.position} • {employee.department}</div>
                          </div>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Search className="h-12 w-12 mx-auto text-gray-400" />
                    <p className="mt-2">No employees found matching your search</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!payslipData && loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl p-6 w-full max-w-md text-center">
          <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
          <p className="mt-4 text-gray-700">Generating payslip data...</p>
        </div>
      </div>
    );
  }

  if (!payslipData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl p-6 w-full max-w-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Payslip Generation</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="h-10 w-10 mx-auto text-red-500" />
            <p className="mt-4">Failed to generate payslip data</p>
            <div className="flex justify-center gap-3 mt-4">
              <button
                onClick={() => setSelectedEmployee(null)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Back
              </button>
              <button
                onClick={fetchPayslipData}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl w-full max-w-2xl">
        <div className="p-4 border-b flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold">Generate Payslip</h2>
            <div className="flex items-center gap-2 mt-1">
              <button 
                onClick={() => setSelectedEmployee(null)}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Change Employee
              </button>
              <span className="text-gray-400">•</span>
              <span className="text-sm text-gray-500">
                {selectedEmployee.name} • {payrollPeriod}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="border rounded-lg p-4">
              <div className="text-sm font-medium text-gray-500">Base Salary</div>
              <div className="text-xl font-semibold mt-1">
                ${payslipData.baseSalary.toFixed(2)}
              </div>
            </div>
            <div className="border rounded-lg p-4">
              <div className="text-sm font-medium text-gray-500">Total Allowances</div>
              <div className="text-xl font-semibold mt-1 text-green-600">
                +${payslipData.totalAllowances.toFixed(2)}
              </div>
            </div>
            <div className="border rounded-lg p-4">
              <div className="text-sm font-medium text-gray-500">Total Deductions</div>
              <div className="text-xl font-semibold mt-1 text-red-600">
                -${payslipData.totalDeductions.toFixed(2)}
              </div>
            </div>
          </div>

          <div className="border rounded-lg p-4 mb-6">
            <div className="flex justify-between items-center">
              <div className="text-sm font-medium text-gray-500">Net Pay</div>
              <div className="text-2xl font-bold">
                ${payslipData.netSalary.toFixed(2)}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-medium">Payslip Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <button
                onClick={() => handleAction("preview")}
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex flex-col items-center"
              >
                <Eye className="h-6 w-6 text-blue-600 mb-2" />
                <span>Preview Payslip</span>
              </button>
              <PDFDownloadLink
                document={<PayslipTemplate employee={selectedEmployee} payrollData={payslipData} period={payrollPeriod} />}
                fileName={`Payslip_${selectedEmployee.name.replace(" ", "_")}_${payrollPeriod.replace(" ", "_")}.pdf`}
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex flex-col items-center"
              >
                <Download className="h-6 w-6 text-blue-600 mb-2" />
                <span>Download PDF</span>
              </PDFDownloadLink>
              <button
                onClick={() => handleAction("email")}
                disabled={emailSent}
                className={`p-4 border rounded-lg flex flex-col items-center ${emailSent ? "border-green-200 bg-green-50" : "border-gray-200 hover:bg-gray-50"}`}
              >
                {emailSent ? (
                  <Check className="h-6 w-6 text-green-600 mb-2" />
                ) : (
                  <Mail className="h-6 w-6 text-blue-600 mb-2" />
                )}
                <span>{emailSent ? "Email Sent" : "Email Payslip"}</span>
              </button>
            </div>
          </div>

          {selectedAction === "email" && loading && (
            <div className="mt-4 p-3 bg-blue-50 text-blue-700 rounded-lg flex items-center gap-2">
              <Loader className="h-4 w-4 animate-spin" />
              <span>Sending email to {selectedEmployee.email}...</span>
            </div>
          )}
        </div>

        <div className="p-4 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default PayslipGeneration;