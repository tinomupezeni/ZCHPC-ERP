import { useState } from "react";
import { 
  Search, Users2, DollarSign, FileText, UserMinus, 
  Award, Clock, Handshake, FileWarning, TrendingUp, 
  Calculator, Building, BriefcaseMedical, Shield, Book, 
  Truck, ChevronRight, LayoutGrid
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import DynamicReport from "./reports/DynamicReports";

// Group reports logically for easier navigation
const REPORT_GROUPS = [
  {
    title: "Core Payroll",
    items: [
      { id: "basicSalary", label: "Basic Salary", icon: DollarSign },
      { id: "paye", label: "PAYE Tax", icon: FileText },
      { id: "nssa", label: "NSSA", icon: Shield },
      { id: "necPension", label: "NEC Pension", icon: Shield },
      { id: "zimdef", label: "ZIMDEF", icon: Building },
      { id: "standardDevLevy", label: "Std Dev Levy", icon: Building },
    ]
  },
  {
    title: "Benefits & Allowances",
    items: [
      { id: "allowances", label: "All Allowances", icon: Award },
      { id: "medicalAid", label: "Medical Aid", icon: BriefcaseMedical },
      { id: "cashInM", label: "Cash in Lieu of Medical", icon: Calculator },
      { id: "funeralPolicy", label: "Funeral Policy", icon: Shield },
      { id: "vehicleBenefit", label: "Vehicle Benefit", icon: Truck },
      { id: "clothing", label: "Clothing Allowance", icon: Award },
      { id: "bonus", label: "Bonus", icon: DollarSign },
    ]
  },
  {
    title: "HR Management",
    items: [
      { id: "leaveBalance", label: "Leave Balances", icon: Users2 },
      { id: "overtime", label: "Overtime", icon: Clock },
      { id: "acting", label: "Acting Allowance", icon: Handshake },
      { id: "promotion", label: "Promotions", icon: TrendingUp },
      { id: "training", label: "Training Costs", icon: Book },
    ]
  },
  {
    title: "Deductions & Loans",
    items: [
      { id: "deductions", label: "General Deductions", icon: UserMinus },
      { id: "loan", label: "Employee Loans", icon: DollarSign },
      { id: "terminalBenefits", label: "Terminal Benefits", icon: FileWarning },
      { id: "retention", label: "Retention", icon: TrendingUp },
    ]
  }
];

const HrReports = () => {
  const [selectedReport, setSelectedReport] = useState("basicSalary");
  const [searchTerm, setSearchTerm] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Find the active label for the header
  const activeReportLabel = REPORT_GROUPS.flatMap(g => g.items).find(i => i.id === selectedReport)?.label;

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-gray-50">
      
      {/* --- Sidebar Navigation --- */}
      <div className={`w-72 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col transition-all duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-72 hidden'}`}>
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <LayoutGrid className="h-6 w-6 text-blue-600" />
            Reports Hub
          </h2>
          <p className="text-xs text-gray-500 mt-1">Financial & HR Analytics</p>
        </div>
        
        <ScrollArea className="flex-1 px-4 py-6">
          <div className="space-y-8">
            {REPORT_GROUPS.map((group) => (
              <div key={group.title}>
                <h3 className="px-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  {group.title}
                </h3>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = selectedReport === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => setSelectedReport(item.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 group ${
                          isActive 
                            ? "bg-blue-50 text-blue-700 shadow-sm" 
                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                        }`}
                      >
                        <span className={`p-1.5 rounded-md ${isActive ? "bg-white text-blue-600 shadow-sm" : "bg-gray-100 text-gray-500 group-hover:bg-white"}`}>
                          <Icon className="h-4 w-4" />
                        </span>
                        {item.label}
                        {isActive && <ChevronRight className="h-4 w-4 ml-auto text-blue-400" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* --- Main Content Area --- */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Header Toolbar */}
        <div className="bg-white border-b border-gray-200 px-8 py-5 flex justify-between items-center sticky top-0 z-10">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{activeReportLabel}</h1>
            <p className="text-sm text-gray-500 mt-1">Viewing real-time data for {new Date().getFullYear()}</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search in report..."
                className="pl-10 bg-gray-50 border-gray-200 focus:bg-white transition-all"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <button className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm">
              Export PDF
            </button>
            <button className="px-4 py-2 bg-blue-600 rounded-lg text-sm font-medium text-white hover:bg-blue-700 shadow-sm shadow-blue-200">
              Export CSV
            </button>
          </div>
        </div>

        {/* Report Container */}
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            
            {/* Summary Cards (Optional Placeholder for now) */}
            {/* <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
               <Card className="border-none shadow-sm bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                 <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-blue-100">Total Amount</CardTitle></CardHeader>
                 <CardContent><div className="text-2xl font-bold">$142,300.00</div></CardContent>
               </Card>
               <Card className="border-none shadow-sm">
                 <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-gray-500">Employees</CardTitle></CardHeader>
                 <CardContent><div className="text-2xl font-bold text-gray-800">142</div></CardContent>
               </Card>
               <Card className="border-none shadow-sm">
                 <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-gray-500">Variance</CardTitle></CardHeader>
                 <CardContent><div className="text-2xl font-bold text-green-600">+2.4%</div></CardContent>
               </Card>
            </div> */}

            {/* The Actual Report Table */}
            <Card className="border-gray-200 shadow-sm overflow-hidden">
              <CardContent className="p-0">
                <DynamicReport reportType={selectedReport} searchTerm={searchTerm} />
              </CardContent>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
};

export default HrReports;