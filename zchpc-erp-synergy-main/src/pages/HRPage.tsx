import { UserPlus, DollarSign, SkipBack } from "lucide-react";
import { Button } from "@/components/ui/button";
import HrDashboard from "@/components/HR/HrDashboard";
import { useEffect, useState } from "react";
import Payroll from "@/components/Payroll/PayrollDashboard";
import Employees from "@/components/HR/employees/Employees";
import Attendance from "@/components/HR/Attendence";
import Recruitment from "@/components/HR/Recruitment";
import TrainingProgramsPage from "@/components/HR/training_development/TrainingPrograms";
import TrainingSessionsPage from "@/components/HR/training_development/TrainingSessions";
import TrainingEnrollmentsPage from "@/components/HR/training_development/TrainingEnrollments";
import TrainingCertificationsPage from "@/components/HR/training_development/TrainingCertifications";
import { Card } from "@/components/ui/card";
import HrReports from "@/components/HR/HrReports";
import CompanyCalendar from "@/components/HR/CompanyCalendar";
import LeaveApplications from "@/components/HR/LeaveApplications";

// HRPage.tsx
interface HRPageProps {
  openTab: string;
}

const HRPage = ({ openTab }: HRPageProps) => {
  const [today, setToday] = useState(""); // Add this state for the date

  useEffect(() => {
    const todayDate = new Date();
    setToday(
      todayDate.toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    );
  }, []);

  const renderContent = () => {
    switch (openTab) {
      case "/hr/hr-payroll":
        return <Payroll />;
      case "/hr/hr-employees":
        return <Employees />;
      case "/hr/hr-attendance":
        return <Attendance />;
      case "/hr/hr-recruitment":
        return <Recruitment />;
      case "/hr/hr-training-programs":
        return <TrainingProgramsPage />;
      case "/hr/hr-training-sessions":
        return <TrainingSessionsPage />;
      case "/hr/hr-training-enrollments":
        return <TrainingEnrollmentsPage />;
      case "/hr/hr-training-certifications":
        return <TrainingCertificationsPage />;
      case "/hr/hr-reports":
        return <HrReports />;
      case "/hr/hr-calendar":
        return <CompanyCalendar />;
      case "/hr/hr-leave":
        return <LeaveApplications />;
      default:
        return <HrDashboard />;
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex justify-between items-center mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Human Resources
            </h1>
            <p className="text-muted-foreground">
              Manage employees, departments and recruitment
            </p>
          </div>
        </div>
        <Card className="shadow-sm flex items-center p-4 bg-primary">
          <div className="text-right">
            <p className="text-xl font-semibold text-white">{today}</p>
          </div>
        </Card>
      </div>
      <hr />
      {renderContent()}
    </div>
  );
};

export default HRPage;
