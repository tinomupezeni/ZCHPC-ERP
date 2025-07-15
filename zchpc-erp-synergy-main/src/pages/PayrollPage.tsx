import PayrollConfig from "@/components/HR/PayrollConfig";
import Recruitment from "@/components/HR/Recruitment";
import Deductions from "@/components/Payroll/Deductions";
import PayrollDashboard from "@/components/Payroll/PayrollDashboard";
import PayslipGeneration from "@/components/Payroll/PayslipGeneration";
import ProcessPayroll from "@/components/Payroll/ProcessPayroll";
import SalarySetup from "@/components/Payroll/SalarySetup";
import TaxConfig from "@/components/TaxConfig";

// HRPage.tsx
interface PayrollProps {
  openTab: string;
}

const PayrollPage = ({openTab} :PayrollProps) => {
  const renderContent = () => {
    switch (openTab){
      case '#payroll-setup':
        return <PayrollDashboard />
      case '#payroll-payslips':
        return <PayslipGeneration />
      case '#payroll-contributions':
        return <Recruitment />
      case '#salary-setup':
        return <SalarySetup />
      case '#deductions':
        return <Deductions />
      case '#process-payroll':
        return <ProcessPayroll />
      case '#tax-tables':
        return <TaxConfig />
      case '#payroll-period':
        return <PayrollConfig />
      default :
       return <PayrollDashboard />
    }
  }
  
  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Payroll</h1>
          <p className="text-muted-foreground">
            Manage employees' salaries, bonuses, etc
          </p>
        </div>
        <div className="flex items-center space-x-2">
          
        </div>
      </div>
      {renderContent()}
    </div>
  );
};

export default PayrollPage;
