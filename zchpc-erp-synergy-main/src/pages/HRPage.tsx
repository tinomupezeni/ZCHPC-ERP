import { UserPlus, DollarSign, SkipBack } from "lucide-react";
import { Button } from "@/components/ui/button";
import HrDashboard from "@/components/HR/HrDashboard";
import { useState } from "react";
import Payroll from "@/components/Payroll/PayrollDashboard";
import Employees from "@/components/HR/employees/Employees";
import Attendance from "@/components/HR/Attendence";
import Recruitment from "@/components/HR/Recruitment";

// HRPage.tsx
interface HRPageProps {
  openTab: string;
}

const HRPage = ({ openTab }: HRPageProps) => {
  const renderContent = () => {
    switch (openTab) {
      case "#hr-payroll":
        return <Payroll />;
      case "#hr-employees":
        return <Employees />;
      case "#hr-attendance":
        return <Attendance />;
      case "#hr-recruitment":
        return <Recruitment />;
      default:
        return <HrDashboard />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Human Resources</h1>
          <p className="text-muted-foreground">
            Manage employees, departments and recruitment
          </p>
        </div>
      </div>
      {renderContent()}
    </div>
  );
};

export default HRPage;
