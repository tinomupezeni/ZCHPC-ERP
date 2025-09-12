import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Search,
  BarChart4,
  Users2,
  DollarSign,
  Clock,
  FileText,
  UserMinus,
  Award,
  Truck,
  BriefcaseMedical,
  Book,
  Building,
  TrendingUp,
  Handshake,
  Shield,
  Calculator,
  FileWarning,
} from "lucide-react";
import { toast } from "sonner";
import Server from "@/server/Server";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import BasicSalaryReport from "./reports/BasicSalaryReport";
import LeaveBalanceReport from "./reports/LeaveBalanceReport";
import PAYEReport from "./reports/PAYEReport";
import DeductionsReport from "./reports/DeductionsReport";
import DynamicReport from "./reports/DynamicReports";

const HrReports = () => {
  const [reports, setReports] = useState({
    leaveBalance: [],
    basicSalary: [],
    paye: [],
    nssa: [],
    deductions: [],
    allowances: [],
    bonus: [],
    overtime: [],
    acting: [],
    terminalBenefits: [],
    retention: [],
    cashInM: [],
    zimdef: [],
    loan: [],
    clothing: [],
    medicalAid: [],
    funeralPolicy: [],
    training: [],
    standardDevLevy: [],
    promotion: [],
    vehicleBenefit: [],
    necPension: [],
  });
  const [selectedReport, setSelectedReport] = useState("leaveBalance");
  const [searchTerm, setSearchTerm] = useState("");

  // useEffect(() => {
  //   // Fetches all the necessary report data from the server.
  //   const fetchReports = async () => {
  //     try {
  //       const response = await Server.fetchFinancialReports();
  //       setReports(response.data);
  //     } catch (error) {
  //       console.error("Failed to fetch reports:", error);
  //       toast.error("Failed to load reports.");
  //     }
  //   };
  //   fetchReports();
  // }, []);

  const getFilteredData = (reportType) => {
    const data = reports[reportType] || [];
    if (!searchTerm) {
      return data;
    }
    return data.filter((item) => {
      const value =
        item.employeeName || item.name || item.description || item.position;
      return value && value.toLowerCase().includes(searchTerm.toLowerCase());
    });
  };

  const renderContent = () => {
    console.log(selectedReport);

    switch (selectedReport) {
      case "leaveBalance":
        return <LeaveBalanceReport />;
      case "basicSalary":
        return <BasicSalaryReport />;
      case "paye":
        return <PAYEReport />;
      case "nssa":
        return <BasicSalaryReport />;
      case "deductions":
        return <DeductionsReport />;
      case "allowances":
        return <BasicSalaryReport />;
      case "overtime":
        return <BasicSalaryReport />;
      case "actingAllowance":
        return <BasicSalaryReport />;
      case "terminalBenefits":
        return <BasicSalaryReport />;
      case "retention":
        return <BasicSalaryReport />;
      case "cashInM":
        return <BasicSalaryReport />;
      case "zimdef":
        return <BasicSalaryReport />;
      case "employeeLoans":
        return <BasicSalaryReport />;
      case "clothingAllowance":
        return <BasicSalaryReport />;
      case "medicalAid":
        return <BasicSalaryReport />;
      case "funeralPolicy":
        return <BasicSalaryReport />;
      case "training":
        return <BasicSalaryReport />;
      case "standardDevLevy":
        return <BasicSalaryReport />;
      case "promotion":
        return <BasicSalaryReport />;
      case "vehicleBenefit":
        return <BasicSalaryReport />;
      case "necPension":
        return <BasicSalaryReport />;
      case "bonus":
        return <BasicSalaryReport />;
      default:
        return (
          <div className="p-4 text-center text-muted-foreground">
            Select a report to view its data.
          </div>
        );
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Financial Reports
          </h1>
          <p className="text-muted-foreground">
            Comprehensive financial and payroll reports for analysis.
          </p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search all reports..."
            className="pl-9"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <Select value={selectedReport} onValueChange={setSelectedReport}>
          <SelectTrigger className="w-full sm:w-[240px]">
            {/* <BarChart4 className="h-4 w-4 mr-2 text-muted-foreground" /> */}
            <SelectValue placeholder="Select a report" />
          </SelectTrigger>
          <SelectContent>
            {/* List of Report SelectItems */}
            <SelectItem value="leaveBalance" className="flex">
              <span>
                <Users2 className="mr-2 h-4 w-4" />
              </span>
              <span className="font-bold">Leave Balance</span>
            </SelectItem>
            <SelectItem value="basicSalary">
              <DollarSign className="mr-2 h-4 w-4" />
              Basic Salary
            </SelectItem>
            <SelectItem value="paye">
              <FileText className="mr-2 h-4 w-4" />
              PAYE
            </SelectItem>
            <SelectItem value="nssa">
              <FileText className="mr-2 h-4 w-4" />
              N.A.S.A
            </SelectItem>
            <SelectItem value="deductions">
              <UserMinus className="mr-2 h-4 w-4" />
              Deductions
            </SelectItem>
            <SelectItem value="allowances">
              <Award className="mr-2 h-4 w-4" />
              Allowances
            </SelectItem>
            <SelectItem value="bonus">
              <DollarSign className="mr-2 h-4 w-4" />
              Bonus
            </SelectItem>
            <SelectItem value="overtime">
              <Clock className="mr-2 h-4 w-4" />
              Overtime/Shortime
            </SelectItem>
            <SelectItem value="acting">
              <Handshake className="mr-2 h-4 w-4" />
              Acting
            </SelectItem>
            <SelectItem value="terminalBenefits">
              <FileWarning className="mr-2 h-4 w-4" />
              Terminal Benefits
            </SelectItem>
            <SelectItem value="retention">
              <TrendingUp className="mr-2 h-4 w-4" />
              Retention
            </SelectItem>
            <SelectItem value="cashInM">
              <Calculator className="mr-2 h-4 w-4" />
              Cash in Lieu of Medical
            </SelectItem>
            <SelectItem value="zimdef">
              <Building className="mr-2 h-4 w-4" />
              ZIMDEF
            </SelectItem>
            <SelectItem value="loan">
              <DollarSign className="mr-2 h-4 w-4" />
              Loan
            </SelectItem>
            <SelectItem value="clothing">
              <Award className="mr-2 h-4 w-4" />
              Clothing
            </SelectItem>
            <SelectItem value="medicalAid">
              <BriefcaseMedical className="mr-2 h-4 w-4" />
              Medical Aid
            </SelectItem>
            <SelectItem value="funeralPolicy">
              <Shield className="mr-2 h-4 w-4" />
              Funeral Policy
            </SelectItem>
            <SelectItem value="training">
              <Book className="mr-2 h-4 w-4" />
              Training
            </SelectItem>
            <SelectItem value="standardDevLevy">
              <Building className="mr-2 h-4 w-4" />
              Standard Dev Levy
            </SelectItem>
            <SelectItem value="promotion">
              <TrendingUp className="mr-2 h-4 w-4" />
              Promotion
            </SelectItem>
            <SelectItem value="vehicleBenefit">
              <Truck className="mr-2 h-4 w-4" />
              Vehicle Benefit
            </SelectItem>
            <SelectItem value="necPension">
              <Shield className="mr-2 h-4 w-4" />
              NEC Pension
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="mt-6">
        <DynamicReport reportType={selectedReport} searchTerm={searchTerm} />
      </div>
    </div>
  );
};

export default HrReports;
