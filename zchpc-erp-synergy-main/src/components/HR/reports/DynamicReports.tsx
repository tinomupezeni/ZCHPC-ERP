import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart3, Download } from "lucide-react";
import { motion } from "framer-motion";
import jsPDF from "jspdf";
import "jspdf-autotable";
import { toast } from "sonner";

// A configuration object for all reports
const reportConfig = {
  leaveBalance: {
    title: "Leave Balance Report",
    endpoint: "http://localhost:8000/api/hr/payrolls/",
    headers: [
      "Employee ID",
      "Name",
      "Leave Type",
      "Days Allocated",
      "Days Taken",
      "Remaining",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.leave_type,
      item.days_allocated,
      item.days_taken,
      item.remaining_days,
    ],
  },
  basicSalary: {
    title: "Basic Salary Report",
    endpoint: "http://localhost:8000/api/payrolls/",
    headers: ["Employee ID", "Name", "Period", "USD Salary", "ZiG Salary"],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.base_salary_usd,
      item.base_salary_zig,
    ],
  },
  paye: {
    title: "ZIMRA PAYE Report",
    endpoint: "http://localhost:8000/api/paye/",
    headers: [
      "Employee ID",
      "Name",
      "Gross Income (USD)",
      "PAYE (USD)",
      "Gross Income (ZiG)",
      "PAYE (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.gross_income_usd,
      item.paye_amount_usd,
      item.gross_income_zig,
      item.paye_amount_zig,
    ],
  },
  nasa: {
    title: "NSSA Report",
    endpoint: "http://localhost:8000/api/nssa/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Contribution (USD)",
      "Contribution (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.nssa_contribution_usd,
      item.nssa_contribution_zig,
    ],
  },
  deductions: {
    title: "Employee Deductions Report",
    endpoint: "http://localhost:8000/api/deductions/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Description",
      "Amount (USD)",
      "Amount (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.description,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  allowances: {
    title: "Employee Allowances Report",
    endpoint: "http://localhost:8000/api/allowances/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Description",
      "Amount (USD)",
      "Amount (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.description,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  nssa: {
    title: "NSSA Report",
    endpoint: "http://localhost:8000/api/nssa/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Contribution (USD)",
      "Contribution (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.nssa_contribution_usd,
      item.nssa_contribution_zig,
    ],
  },
  loan: {
    title: "Employee Loans Report",
    endpoint: "http://localhost:8000/api/loan/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Loan Amount (USD)",
      "Loan Amount (ZiG)",
      "Repayment (USD)",
      "Repayment (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.loan_amount_usd,
      item.loan_amount_zig,
      item.repayment_amount_usd,
      item.repayment_amount_zig,
    ],
  },
  clothing: {
    title: "Clothing Allowance Report",
    endpoint: "http://localhost:8000/api/clothing/",
    headers: ["Employee ID", "Name", "Period", "Amount (USD)", "Amount (ZiG)"],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  medicalAid: {
    title: "Medical Aid Report",
    endpoint: "http://localhost:8000/api/medicalaid/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Contribution (USD)",
      "Contribution (ZiG)",
      "Status",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.contribution_usd,
      item.contribution_zig,
      item.status,
    ],
  },
  funeralPolicy: {
    title: "Funeral Policy Report",
    endpoint: "http://localhost:8000/api/funeralpolicy/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Contribution (USD)",
      "Contribution (ZiG)",
      "Status",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.contribution_usd,
      item.contribution_zig,
      item.status,
    ],
  },
  training: {
    title: "Training Report",
    endpoint: "http://localhost:8000/api/training/",
    headers: [
      "Employee ID",
      "Name",
      "Training",
      "Start Date",
      "End Date",
      "Cost (USD)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.description,
      item.start_date,
      item.end_date,
      item.cost_usd,
    ],
  },
  standardDevLevy: {
    title: "Standard Dev Levy Report",
    endpoint: "http://localhost:8000/api/stddevlevy/",
    headers: ["Employee ID", "Name", "Period", "Amount (USD)", "Amount (ZiG)"],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  promotion: {
    title: "Promotion Report",
    endpoint: "http://localhost:8000/api/promotion/",
    headers: [
      "Employee ID",
      "Name",
      "Previous Position",
      "New Position",
      "Effective Date",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.previous_position,
      item.new_position,
      item.effective_date,
    ],
  },
  vehicleBenefit: {
    title: "Vehicle Benefit Report",
    endpoint: "http://localhost:8000/api/vehiclebenefit/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Benefit Amount (USD)",
      "Benefit Amount (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.benefit_usd,
      item.benefit_zig,
    ],
  },
  necPension: {
    title: "NEC Pension Report",
    endpoint: "http://localhost:8000/api/necpension/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Contribution (USD)",
      "Contribution (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.contribution_usd,
      item.contribution_zig,
    ],
  },
  bonus: {
    title: "Bonus Report",
    endpoint: "http://localhost:8000/api/bonus/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Bonus Type",
      "Amount (USD)",
      "Amount (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.bonus_type,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  overtime: {
    title: "Overtime/Shortime Report",
    endpoint: "http://localhost:8000/api/overtime/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Hours",
      "Rate (USD)",
      "Amount (USD)",
      "Amount (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.hours,
      item.rate_usd,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  acting: {
    title: "Acting Allowance Report",
    endpoint: "http://localhost:8000/api/acting/",
    headers: [
      "Employee ID",
      "Name",
      "Period",
      "Description",
      "Amount (USD)",
      "Amount (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.description,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  terminalBenefits: {
    title: "Terminal Benefits Report",
    endpoint: "http://localhost:8000/api/terminalbenefits/",
    headers: [
      "Employee ID",
      "Name",
      "Termination Date",
      "Benefit Type",
      "Amount (USD)",
      "Amount (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.termination_date,
      item.benefit_type,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  retention: {
    title: "Retention Bonus Report",
    endpoint: "http://localhost:8000/api/retention/",
    headers: [
      "Employee ID",
      "Name",
      "Bonus Date",
      "Amount (USD)",
      "Amount (ZiG)",
    ],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.bonus_date,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  cashInM: {
    title: "Cash in Lieu of Medical Aid Report",
    endpoint: "http://localhost:8000/api/cashinlieu/",
    headers: ["Employee ID", "Name", "Period", "Amount (USD)", "Amount (ZiG)"],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  zimdef: {
    title: "ZIMDEF Report",
    endpoint: "http://localhost:8000/api/zimdef/",
    headers: ["Employee ID", "Name", "Period", "Amount (USD)", "Amount (ZiG)"],
    dataMap: (item) => [
      item.employee.employeeid,
      `${item.employee.firstname} ${item.employee.surname}`,
      item.period,
      item.amount_usd,
      item.amount_zig,
    ],
  },
  // Add other reports here following the same pattern
};

export default function DynamicReport({ reportType }) {
  const [reportData, setReportData] = useState([]);
  const config = reportConfig[reportType];

  const today = new Date();
  const formattedDate = `${today.getDate()}/${
    today.getMonth() + 1
  }/${today.getFullYear()}`;

  useEffect(() => {
    if (!config) return;

    const fetchData = async () => {
      try {
        const res = await fetch(config.endpoint);

        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        console.log(data);
        setReportData(data);
      } catch (err) {
        console.error(`Error fetching ${config.title}:`, err);
        toast.error(`Failed to load ${config.title}.`);
      }
    };

    fetchData();
  }, [reportType, config]); // Re-run effect when reportType changes

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text(config.title, 14, 16);
    doc.autoTable({
      startY: 20,
      head: [config.headers],
      body: reportData.map(config.dataMap),
    });
    doc.save(`${reportType}_report.pdf`);
  };

  if (!config) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        Select a report to view its data.
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Card className="p-4 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">{config.title}</h2>
          <Button onClick={exportPDF}>
            <Download className="w-4 h-4 mr-2" /> Export PDF
          </Button>
        </div>
        <div className="border border-black">
          {config.title === "Leave Balance Report" && (
            <div className="w-full border-b border-black mb-5">
              <div className="flex align-center text-center justify-center font-semibold">
                <div>
                  <h1 className="uppercase">Leave Balance Report</h1>
                  <p>Department of Human Resources</p>
                </div>
              </div>
              <div className="flex justify-between font-semibold mx-7">
                <div>
                  <p>RUN DATE : {formattedDate}</p>
                  <p>PAGE : 1</p>
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="h-6 w-6 text-primary" />
                    <span className="text-lg font-semibold">ZCHPC ERP</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-black">
                <thead className="bg-white">
                  <tr>
                    {config.headers.map((header) => (
                      <th key={header} className="p-2 border">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {reportData.length > 0 ? (
                    reportData.map((item, index) => (
                      <tr key={index}>
                        {config.dataMap(item).map((cell, cellIndex) => (
                          <td key={cellIndex} className="p-2 border">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={config.headers.length}
                        className="p-4 text-center text-gray-500"
                      >
                        No data available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </div>
      </Card>
    </motion.div>
  );
}
