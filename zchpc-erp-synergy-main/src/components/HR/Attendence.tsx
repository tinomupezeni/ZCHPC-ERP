import { useState, useEffect, useRef } from "react";
import { Search, Calendar, MoreVertical, Filter, Download, ChevronDown, Clock, Check, X, Upload } from "lucide-react";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import Server from "@/services/Server";
import { toast } from "sonner";

// Helper: resolve a "Time Range" selection to a concrete [start, end] date pair.
// "Custom Range" is handled by the caller via explicit customStart/customEnd instead.
const resolveDateRange = (timeRange: string): { start: string; end: string } | null => {
  const today = new Date();
  const toISO = (d: Date) => d.toISOString().slice(0, 10);

  if (timeRange === "Last 7 Days") {
    const start = new Date(today);
    start.setDate(start.getDate() - 6);
    return { start: toISO(start), end: toISO(today) };
  }
  if (timeRange === "Last 30 Days") {
    const start = new Date(today);
    start.setDate(start.getDate() - 29);
    return { start: toISO(start), end: toISO(today) };
  }
  if (timeRange === "This Month") {
    const start = new Date(today.getFullYear(), today.getMonth(), 1);
    return { start: toISO(start), end: toISO(today) };
  }
  return null;
};

// Helper: display time as HH:MM for UI
const formatTime = (timeStr) => {
  if (!timeStr) return "--";
  try {
    if (typeof timeStr === "string" && timeStr.match(/^\d{1,2}:\d{2}(?::\d{2})?$/)) {
      const [hours, minutes] = timeStr.split(":");
      return `${hours.padStart(2, "0")}:${minutes.padStart(2, "0")}`;
    }
    const date = new Date(timeStr);
    if (!isNaN(date.getTime())) {
      const hh = date.getHours().toString().padStart(2, "0");
      const mm = date.getMinutes().toString().padStart(2, "0");
      return `${hh}:${mm}`;
    }
    return timeStr;
  } catch {
    return String(timeStr);
  }
};

// Helper: strict HH:MM for CSV
const formatTimeHHMM = (value: any): string => {
  if (!value) return "";
  try {
    if (typeof value === "string") {
      const m = value.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
      if (m) {
        const hh = m[1].padStart(2, "0");
        const mm = m[2].padStart(2, "0");
        return `${hh}:${mm}`;
      }
      const d = new Date(value);
      if (!isNaN(d.getTime())) {
        const hh = d.getHours().toString().padStart(2, "0");
        const mm = d.getMinutes().toString().padStart(2, "0");
        return `${hh}:${mm}`;
      }
      return value;
    }
    if (value instanceof Date) {
      const hh = value.getHours().toString().padStart(2, "0");
      const mm = value.getMinutes().toString().padStart(2, "0");
      return `${hh}:${mm}`;
    }
    return String(value ?? "");
  } catch {
    return String(value ?? "");
  }
};

const Attendance = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState("Last 7 Days");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [selectedDepartment, setSelectedDepartment] = useState(""); // "" = All Departments
  const [departments, setDepartments] = useState<{ id: number | string; name: string }[]>([]);

  useEffect(() => {
    fetchDepartments();
  }, []);

  useEffect(() => {
    fetchAttendanceRecords();
  }, [selectedDepartment, timeRange, customStart, customEnd]);

  const fetchAttendanceRecords = async () => {
    setLoading(true);
    try {
      const range =
        timeRange === "Custom Range"
          ? customStart && customEnd
            ? { start: customStart, end: customEnd }
            : null
          : resolveDateRange(timeRange);

      const response = await Server.fetchAttendanceRecords({
        department_id: selectedDepartment || undefined,
        start_date: range?.start,
        end_date: range?.end,
        // Frontend paginates client-side, so pull the largest page in one go.
        page_size: 200,
      });

      const results = response.data?.results;
      if (Array.isArray(results)) {
        const formattedRecords = results.map(record => ({
          name: record.employee_name || '',
          'job no': record.employee_id ?? '',
          date: record.record_date,
          'time in': record.time_in,
          'time out': record.time_out,
        }));
        setAttendanceRecords(formattedRecords);
      } else {
        console.warn('Unexpected data format received:', response.data);
        setAttendanceRecords([]);
      }
    } catch (error) {
      console.error("Error fetching attendance records:", error);
      toast.error('Failed to load attendance records. Please try again.');
      setAttendanceRecords([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await Server.fetchDepartments();
      setDepartments(response.data || []);
    } catch (error) {
      console.error("Error fetching departments:", error);
    }
  };

  const filteredRecords = attendanceRecords.filter(record => {
    return (
      (record.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(record['job no'] || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  // Pagination logic
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredRecords.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredRecords.length / itemsPerPage);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const exportToCSV = () => {
    // Align export with normalized fields
    const headers = ["name", "job no", "date", "time in", "time out"];
    const csvContent = [
      headers.join(","),
      ...filteredRecords.map(record => {
        const row = [
          record.name || "",
          record['job no'] || "",
          record.date || "",
          formatTimeHHMM(record['time in']) || "",
          formatTimeHHMM(record['time out']) || "",
        ];
        return row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",");
      })
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `attendance_records_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check if file is an Excel or CSV file
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'text/csv',
      'application/csv',
      'application/vnd.oasis.opendocument.spreadsheet'
    ];

    if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv|ods)$/i)) {
      toast.error('Please upload a valid Excel or CSV file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress (since we can't track actual upload progress with the current Server implementation)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90; // Hold at 90% until the request completes
          }
          return prev + 10;
        });
      }, 200);

      const response = await Server.uploadAttendance(file);
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      // Show success message with stats
      const { created, updated, errors } = response.data;
      let message = `Success! ${created} records created, ${updated} updated.`;
      if (errors && errors.length > 0) {
        message += ` ${errors.length} records had errors.`;
        console.error('Upload errors:', errors);
      }
      
      toast.success(message);
      
      // Refresh the attendance data
      fetchAttendanceRecords();
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload file. Please try again.');
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 1000);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="min-h-screen p-6 bg-gray-50">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Attendance Management</h1>
          <p className="text-sm text-gray-500">
            {filteredRecords.length} {filteredRecords.length === 1 ? "record" : "records"} found
          </p>
        </div>
        <div className="flex gap-3">
          <div className="flex gap-3">
            <button
              onClick={exportToCSV}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 transition-colors border border-gray-300 rounded-lg hover:bg-gray-100"
              disabled={isUploading}
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            <button
              onClick={triggerFileInput}
              className={`flex items-center gap-2 px-4 py-2 text-white transition-colors bg-blue-600 rounded-lg hover:bg-blue-700 ${isUploading ? 'opacity-70 cursor-not-allowed' : ''}`}
              disabled={isUploading}
            >
              {isUploading ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Bulk Upload
                </>
              )}
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".xlsx, .xls, .csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, text/csv, application/csv"
              className="hidden"
              disabled={isUploading}
            />
          </div>
        </div>
      </div>

      {isUploading && (
        <div className="p-4 mb-4 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-800">Uploading attendance data...</span>
            <span className="text-sm font-medium text-blue-800">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      <div className="mb-8 bg-white border border-gray-200 rounded-lg shadow-sm">
        <div className="p-4 border-b">
          <div className="flex flex-col items-start gap-4 md:flex-row md:items-center">
            <div className="relative flex-1 w-full">
              <Search className="absolute w-5 h-5 text-gray-400 transform -translate-y-1/2 left-3 top-1/2" />
              <input
                type="text"
                placeholder="Search by name or employee ID..."
                className="w-full py-2 pl-10 pr-4 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                  title="Department"
                  className="px-4 py-2 pr-8 border rounded-lg appearance-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={selectedDepartment}
                  onChange={(e) => {
                    setSelectedDepartment(e.target.value);
                    setCurrentPage(1);
                  }}
                >
                  <option value="">All Departments</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute w-4 h-4 text-gray-400 transform -translate-y-1/2 right-3 top-1/2" />
              </div>
              <div className="relative">
                <select
                title="Time Range"
                  className="px-4 py-2 pr-8 border rounded-lg appearance-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={timeRange}
                  onChange={(e) => {
                    setTimeRange(e.target.value);
                    setCurrentPage(1);
                  }}
                >
                  <option>Last 7 Days</option>
                  <option>Last 30 Days</option>
                  <option>This Month</option>
                  <option>Custom Range</option>
                </select>
                <ChevronDown className="absolute w-4 h-4 text-gray-400 transform -translate-y-1/2 right-3 top-1/2" />
              </div>
              {timeRange === "Custom Range" && (
                <>
                  <input
                    type="date"
                    aria-label="Start date"
                    className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={customStart}
                    onChange={(e) => setCustomStart(e.target.value)}
                  />
                  <input
                    type="date"
                    aria-label="End date"
                    className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={customEnd}
                    onChange={(e) => setCustomEnd(e.target.value)}
                  />
                </>
              )}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                  Name
                </th>
                <th scope="col" className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                  Job No
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th scope="col" className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                  Time In
                </th>
                <th scope="col" className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                  Time Out
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center">
                    <Clock className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                    <p className="mt-2 text-sm text-gray-500">Loading attendance records...</p>
                  </td>
                </tr>
              ) : currentItems?.length > 0 ? (
                currentItems?.map((record, index) => (
                  <tr key={`${record['job no']}-${record.date}-${index}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                          {(record.name || "").split(' ').map(n => n[0]).join('').toUpperCase() || '--'}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {record.name || '--'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record['job no'] || '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record.date ? new Date(record.date).toLocaleDateString() : '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record['time in'] ? formatTime(record['time in']) : '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record['time out'] ? formatTime(record['time out']) : '--'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center">
                    <div className="flex flex-col items-center justify-center">
                      <Search className="w-12 h-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No attendance records found</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {searchTerm ? "Try adjusting your search or filter" : "No records available for selected period"}
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
          <div className="flex items-center justify-between px-6 py-4 border-t">
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
    </div>
  );
};

export default Attendance;