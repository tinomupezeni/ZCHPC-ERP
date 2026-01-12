import { useState } from "react";
import {
  Search,
  FileDown,
  Printer,
  Filter,
  ChevronDown,
  LayoutDashboard,
  Table as TableIcon,
  RefreshCw,
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
import DynamicReport from "./reports/DynamicReports";

const REPORT_OPTIONS = [
  {
    group: "Core Payroll",
    items: ["basicSalary", "paye", "nssa", "necPension", "zimdef"],
  },
  {
    group: "Benefits",
    items: ["allowances", "medicalAid", "bonus", "vehicleBenefit"],
  },
  {
    group: "HR Analytics",
    items: ["leaveBalance", "overtime", "training", "promotion"],
  },
  { group: "Deductions", items: ["deductions", "loan", "terminalBenefits"] },
];

const HrReports = () => {
  const [selectedReport, setSelectedReport] = useState("basicSalary");
  const [searchTerm, setSearchTerm] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Helper to format the ID back to a readable label
  const formatLabel = (id: string) =>
    id.replace(/([A-Z])/g, " $1").replace(/^./, (str) => str.toUpperCase());

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000); // Simulate reload
  };

  return (
    <div className="flex flex-col space-y-6 min-h-screen pb-10">
      {/* --- Action Header --- */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div className="space-y-3 flex-1">
          <label className="text-xs font-bold uppercase tracking-wider text-gray-500">
            Select Report Type
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <Select value={selectedReport} onValueChange={setSelectedReport}>
              <SelectTrigger className="w-[280px] bg-gray-50 border-gray-200 font-medium h-11">
                <SelectValue placeholder="Choose a report..." />
              </SelectTrigger>
              <SelectContent>
                {REPORT_OPTIONS.map((group) => (
                  <div key={group.group}>
                    <div className="px-2 py-1.5 text-xs font-semibold text-blue-600 bg-blue-50/50">
                      {group.group}
                    </div>
                    {group.items.map((id) => (
                      <SelectItem key={id} value={id}>
                        {formatLabel(id)}
                      </SelectItem>
                    ))}
                  </div>
                ))}
              </SelectContent>
            </Select>

            <div className="relative w-full md:w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Quick filter results..."
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
            className={isRefreshing ? "animate-spin" : ""}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="outline" className="gap-2">
            <Printer className="h-4 w-4" /> Print
          </Button>
          <Button
            variant="default"
            className="gap-2 bg-blue-600 hover:bg-blue-700 shadow-md"
          >
            <FileDown className="h-4 w-4" /> Export Report
          </Button>
        </div>
      </div>

      {/* --- Summary Bar --- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Report Period"
          value="Dec 2025"
          subtitle="Current Cycle"
        />
        <SummaryCard
          title="Total Records"
          value="1,240"
          subtitle="Active Employees"
        />
        <SummaryCard
          title="Status"
          value="Verified"
          subtitle="By Finance Dept"
          accent="text-green-600"
        />
        <SummaryCard
          title="Currency"
          value="USD"
          subtitle="Local Equivalent: ZIG"
        />
      </div>

      {/* --- Main Data Table Area --- */}
      <Card className="border-gray-200 shadow-lg overflow-hidden rounded-xl">
        <div className="bg-gray-50/50 border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <TableIcon className="h-5 w-5 text-gray-400" />
            <h3 className="font-semibold text-gray-700">
              {formatLabel(selectedReport)} Detailed View
            </h3>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500" /> Live Data
            </span>
            <span>Last Updated: Just now</span>
          </div>
        </div>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <DynamicReport
              reportType={selectedReport}
              searchTerm={searchTerm}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Sub-component for clean organization
const SummaryCard = ({
  title,
  value,
  subtitle,
  accent = "text-gray-900",
}: any) => (
  <Card className="border-none shadow-sm bg-white">
    <CardContent className="p-5">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-tight">
        {title}
      </p>
      <div className={`text-2xl font-bold mt-1 ${accent}`}>{value}</div>
      <p className="text-[11px] text-gray-400 mt-0.5">{subtitle}</p>
    </CardContent>
  </Card>
);

export default HrReports;
