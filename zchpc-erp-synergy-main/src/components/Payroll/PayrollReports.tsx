import { useState, useEffect, useRef } from "react";
import {
  Search,
  FileDown,
  Printer,
  RefreshCw,
  DollarSign,
  Users,
  TrendingDown,
  Wallet,
  FileText,
  Download,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { fetchReportData, fetchReportSummary, exportReportToCSV, ReportSummary, ReportData } from "@/services/reports.services";
import { getDepartment } from "@/services/hr.services";
import { formatUSD, formatZIG } from "@/components/ui/utils";

// Payroll-specific report types
const PAYROLL_REPORTS = [
  { id: "basicSalary", name: "Basic Salary Report", icon: DollarSign },
  { id: "paye", name: "PAYE Tax Report", icon: FileText },
  { id: "nssa", name: "NSSA Contributions", icon: Users },
  { id: "allowances", name: "Allowances Report", icon: Wallet },
  { id: "deductions", name: "Deductions Report", icon: TrendingDown },
];

// Column definitions for each report type
const REPORT_COLUMNS: Record<string, { key: string; label: string; format?: "currency" | "percent" }[]> = {
  basicSalary: [
    { key: "employee_id", label: "Employee ID" },
    { key: "employee_name", label: "Employee Name" },
    { key: "department", label: "Department" },
    { key: "period", label: "Period" },
    { key: "base_salary_usd", label: "Base Salary (USD)", format: "currency" },
    { key: "base_salary_zig", label: "Base Salary (ZiG)", format: "currency" },
    { key: "net_salary_usd", label: "Net Salary (USD)", format: "currency" },
    { key: "status", label: "Status" },
  ],
  paye: [
    { key: "employee_id", label: "Employee ID" },
    { key: "employee_name", label: "Employee Name" },
    { key: "department", label: "Department" },
    { key: "period", label: "Period" },
    { key: "gross_salary_usd", label: "Gross Salary (USD)", format: "currency" },
    { key: "paye_usd", label: "PAYE (USD)", format: "currency" },
    { key: "paye_zig", label: "PAYE (ZiG)", format: "currency" },
    { key: "aids_levy_usd", label: "AIDS Levy (USD)", format: "currency" },
  ],
  nssa: [
    { key: "employee_id", label: "Employee ID" },
    { key: "employee_name", label: "Employee Name" },
    { key: "nssa_number", label: "NSSA Number" },
    { key: "department", label: "Department" },
    { key: "period", label: "Period" },
    { key: "employee_contribution_usd", label: "Employee Contrib. (USD)", format: "currency" },
    { key: "employer_contribution_usd", label: "Employer Contrib. (USD)", format: "currency" },
    { key: "total_nssa_usd", label: "Total NSSA (USD)", format: "currency" },
  ],
  allowances: [
    { key: "employee_id", label: "Employee ID" },
    { key: "employee_name", label: "Employee Name" },
    { key: "department", label: "Department" },
    { key: "period", label: "Period" },
    { key: "base_salary_usd", label: "Base Salary (USD)", format: "currency" },
    { key: "total_allowances_usd", label: "Total Allowances (USD)", format: "currency" },
    { key: "total_allowances_zig", label: "Total Allowances (ZiG)", format: "currency" },
    { key: "gross_salary_usd", label: "Gross Salary (USD)", format: "currency" },
  ],
  deductions: [
    { key: "employee_id", label: "Employee ID" },
    { key: "employee_name", label: "Employee Name" },
    { key: "department", label: "Department" },
    { key: "period", label: "Period" },
    { key: "gross_salary_usd", label: "Gross Salary (USD)", format: "currency" },
    { key: "paye_usd", label: "PAYE (USD)", format: "currency" },
    { key: "nssa_usd", label: "NSSA (USD)", format: "currency" },
    { key: "total_deductions_usd", label: "Total Deductions (USD)", format: "currency" },
    { key: "net_salary_usd", label: "Net Salary (USD)", format: "currency" },
  ],
};

const PayrollReports = () => {
  const [selectedReport, setSelectedReport] = useState("basicSalary");
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("all");
  const [departments, setDepartments] = useState<{ id: number; name: string }[]>([]);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [periods, setPeriods] = useState<{ period: string; label: string }[]>([]);
  const [reportData, setReportData] = useState<ReportData[]>([]);

  // Generate last 12 months as periods
  useEffect(() => {
    const generatedPeriods: { period: string; label: string }[] = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const period = date.toISOString().split("T")[0];
      const label = date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
      generatedPeriods.push({ period, label });
    }
    setPeriods(generatedPeriods);
    if (generatedPeriods.length > 0) {
      setSelectedPeriod(generatedPeriods[0].period);
    }
  }, []);

  // Fetch departments
  useEffect(() => {
    const loadDepartments = async () => {
      try {
        const response = await getDepartment();
        const depts = Array.isArray(response) ? response : response.data || [];
        setDepartments(depts);
      } catch (error) {
        console.error("Failed to load departments", error);
      }
    };
    loadDepartments();
  }, []);

  // Fetch summary data
  useEffect(() => {
    const loadSummary = async () => {
      try {
        const data = await fetchReportSummary(selectedPeriod);
        setSummary(data);
      } catch (error) {
        console.error("Failed to load summary", error);
      }
    };
    loadSummary();
  }, [selectedPeriod]);

  // Fetch report data when filters change
  useEffect(() => {
    const loadReportData = async () => {
      setIsLoading(true);
      try {
        const data = await fetchReportData(selectedReport, {
          period: selectedPeriod,
          department: selectedDepartment === "all" ? "" : selectedDepartment,
        });
        setReportData(data);
      } catch (error) {
        console.error("Failed to load report data", error);
        toast.error("Failed to load report data");
        setReportData([]);
      } finally {
        setIsLoading(false);
      }
    };
    if (selectedPeriod) {
      loadReportData();
    }
  }, [selectedReport, selectedPeriod, selectedDepartment]);

  // Format currency
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value || 0);

  // Get current report config
  const currentReport = PAYROLL_REPORTS.find(r => r.id === selectedReport);
  const columns = REPORT_COLUMNS[selectedReport] || [];

  // Filter data by search term
  const filteredData = reportData.filter((row) =>
    Object.values(row).some(
      (val) =>
        val &&
        String(val).toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  // Handle refresh
  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      const data = await fetchReportData(selectedReport, {
        period: selectedPeriod,
        department: selectedDepartment === "all" ? "" : selectedDepartment,
      });
      setReportData(data);
      toast.success("Report refreshed");
    } catch (error) {
      toast.error("Failed to refresh report");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle export
  const handleExport = () => {
    if (filteredData.length === 0) {
      toast.error("No data to export");
      return;
    }
    const reportName = currentReport?.name || "report";
    const periodLabel = periods.find(p => p.period === selectedPeriod)?.label || "all";
    exportReportToCSV(filteredData, `${reportName}_${periodLabel}`.replace(/\s+/g, "_"));
    toast.success("Report exported successfully");
  };

  // Handle print
  const handlePrint = () => {
    window.print();
  };

  // Format cell value
  const formatCellValue = (value: any, format?: string) => {
    if (value === null || value === undefined) return "-";
    if (format === "currency") return formatCurrency(Number(value));
    if (format === "percent") return `${(Number(value) * 100).toFixed(1)}%`;
    return String(value);
  };

  return (
    <div className="flex flex-col space-y-6 min-h-screen pb-10">
      {/* Action Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div className="space-y-3 flex-1">
          <label className="text-xs font-bold uppercase tracking-wider text-gray-500">
            Payroll Reports
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <Select value={selectedReport} onValueChange={setSelectedReport}>
              <SelectTrigger className="w-[220px] bg-gray-50 border-gray-200 font-medium h-11">
                <SelectValue placeholder="Choose a report..." />
              </SelectTrigger>
              <SelectContent>
                {PAYROLL_REPORTS.map((report) => (
                  <SelectItem key={report.id} value={report.id}>
                    <div className="flex items-center gap-2">
                      <report.icon className="h-4 w-4 text-gray-500" />
                      {report.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger className="w-[180px] bg-gray-50 border-gray-200 font-medium h-11">
                <SelectValue placeholder="Select period..." />
              </SelectTrigger>
              <SelectContent>
                {periods.map((p) => (
                  <SelectItem key={p.period} value={p.period}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedDepartment} onValueChange={setSelectedDepartment}>
              <SelectTrigger className="w-[180px] bg-gray-50 border-gray-200 font-medium h-11">
                <SelectValue placeholder="All Departments" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Departments</SelectItem>
                {departments.map((d) => (
                  <SelectItem key={d.id} value={String(d.id)}>
                    {d.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div className="relative w-full md:w-56">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search results..."
                className="pl-10 h-11 bg-gray-50 border-gray-200"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={isLoading}
            className={isLoading ? "animate-spin" : ""}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="outline" className="gap-2" onClick={handlePrint}>
            <Printer className="h-4 w-4" /> Print
          </Button>
          <Button
            variant="default"
            className="gap-2 bg-blue-600 hover:bg-blue-700 shadow-md"
            onClick={handleExport}
          >
            <FileDown className="h-4 w-4" /> Export CSV
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Employees"
          value={summary?.total_employees?.toLocaleString() || "0"}
          subtitle="Active workforce"
          icon={Users}
        />
        <SummaryCard
          title="Total Gross Salary"
          value={formatCurrency(summary?.total_gross_salary_usd || 0)}
          subtitle={`${summary?.payroll_records || 0} payroll records`}
          icon={DollarSign}
        />
        <SummaryCard
          title="Total Net Salary"
          value={formatCurrency(summary?.total_net_salary_usd || 0)}
          subtitle="After deductions"
          icon={Wallet}
          accent="text-green-600"
        />
        <SummaryCard
          title="Total Deductions"
          value={formatCurrency((summary?.total_paye_usd || 0) + (summary?.total_nssa_usd || 0) + (summary?.total_deductions_usd || 0))}
          subtitle="PAYE, NSSA & Other"
          icon={TrendingDown}
          accent="text-orange-600"
        />
      </div>

      {/* Data Table */}
      <Card className="border-gray-200 shadow-lg overflow-hidden rounded-xl">
        <div className="bg-gray-50/50 border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            {currentReport && <currentReport.icon className="h-5 w-5 text-blue-600" />}
            <h3 className="font-semibold text-gray-700">
              {currentReport?.name || "Report"}
            </h3>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500" /> Live Data
            </span>
            <span>
              {filteredData.length} records
            </span>
            <span>
              Period: {periods.find((p) => p.period === selectedPeriod)?.label || "All"}
            </span>
          </div>
        </div>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-16">
                <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
                <span className="ml-2 text-gray-500">Loading report data...</span>
              </div>
            ) : filteredData.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                <FileText className="h-12 w-12 mb-2" />
                <p>No data available for the selected period</p>
                <p className="text-sm">Try selecting a different period or check payroll processing</p>
              </div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {columns.map((col) => (
                      <th
                        key={col.key}
                        className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        {col.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredData.map((row, rowIndex) => (
                    <tr key={row.id || rowIndex} className="hover:bg-gray-50">
                      {columns.map((col) => (
                        <td key={col.key} className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                          {formatCellValue(row[col.key], col.format)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Totals Footer */}
      {filteredData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-gray-500">Total Records:</span>{" "}
              <span className="font-semibold">{filteredData.length}</span>
            </div>
            {selectedReport === "basicSalary" && (
              <>
                <div>
                  <span className="text-gray-500">Total Base Salary (USD):</span>{" "}
                  <span className="font-semibold text-green-600">
                    {formatCurrency(filteredData.reduce((sum, r) => sum + (Number(r.base_salary_usd) || 0), 0))}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Total Net Salary (USD):</span>{" "}
                  <span className="font-semibold text-blue-600">
                    {formatCurrency(filteredData.reduce((sum, r) => sum + (Number(r.net_salary_usd) || 0), 0))}
                  </span>
                </div>
              </>
            )}
            {selectedReport === "paye" && (
              <div>
                <span className="text-gray-500">Total PAYE (USD):</span>{" "}
                <span className="font-semibold text-orange-600">
                  {formatCurrency(filteredData.reduce((sum, r) => sum + (Number(r.paye_usd) || 0), 0))}
                </span>
              </div>
            )}
            {selectedReport === "nssa" && (
              <div>
                <span className="text-gray-500">Total NSSA (USD):</span>{" "}
                <span className="font-semibold text-orange-600">
                  {formatCurrency(filteredData.reduce((sum, r) => sum + (Number(r.total_nssa_usd) || 0), 0))}
                </span>
              </div>
            )}
            {selectedReport === "deductions" && (
              <div>
                <span className="text-gray-500">Total Deductions (USD):</span>{" "}
                <span className="font-semibold text-red-600">
                  {formatCurrency(filteredData.reduce((sum, r) => sum + (Number(r.total_deductions_usd) || 0), 0))}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Summary Card Component
const SummaryCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  accent = "text-gray-900",
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ElementType;
  accent?: string;
}) => (
  <Card className="border-none shadow-sm bg-white">
    <CardContent className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-tight">
            {title}
          </p>
          <div className={`text-2xl font-bold mt-1 ${accent}`}>{value}</div>
          <p className="text-[11px] text-gray-400 mt-0.5">{subtitle}</p>
        </div>
        <div className="p-2 bg-blue-50 rounded-lg">
          <Icon className="h-5 w-5 text-blue-600" />
        </div>
      </div>
    </CardContent>
  </Card>
);

export default PayrollReports;
