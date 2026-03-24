// src/components/BasicSalaryReport.jsx
import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { motion } from "framer-motion";
import jsPDF from "jspdf";
import "jspdf-autotable";

const API_URL = import.meta.env.VITE_API_URL || '';

export default function BasicSalaryReport() {
  const [payrolls, setPayrolls] = useState([]);
  console.log('we in it');


  useEffect(() => {
    fetch(`${API_URL}/api/payrolls/`)
      .then((res) => res.json())
      .then((data) => setPayrolls(data))
      .catch((err) => console.error("Error fetching payrolls:", err));
  }, []);

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text("Basic Salary Report", 14, 16);
    doc.autoTable({
      startY: 20,
      head: [["Employee ID", "Name", "Department", "Period", "USD Salary", "ZiG Salary", "Exchange Rate", "Net USD", "Net ZiG", "Status"]],
      body: payrolls.map((p) => [
        p.employee.employeeid,
        `${p.employee.firstname} ${p.employee.surname}`,
        p.employee.department,
        p.period,
        p.base_salary_usd,
        p.base_salary_zig,
        p.exchange_rate,
        p.net_salary_usd,
        p.net_salary_zig,
        p.status,
      ]),
    });
    doc.save("basic_salary_report.pdf");
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Card className="p-4 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Basic Salary Report</h2>
          <Button onClick={exportPDF}>
            <Download className="w-4 h-4 mr-2" /> Export PDF
          </Button>
        </div>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border">
              <thead className="bg-gray-100">
                <tr>
                  <th className="p-2 border">Employee ID</th>
                  <th className="p-2 border">Name</th>
                  <th className="p-2 border">Department</th>
                  <th className="p-2 border">Period</th>
                  <th className="p-2 border">USD Salary</th>
                  <th className="p-2 border">ZiG Salary</th>
                  <th className="p-2 border">Exchange Rate</th>
                  <th className="p-2 border">Net USD</th>
                  <th className="p-2 border">Net ZiG</th>
                  <th className="p-2 border">Status</th>
                </tr>
              </thead>
              <tbody>
                {payrolls.map((p) => (
                  <tr key={`${p.employee.employeeid}-${p.period}`}>
                    <td className="p-2 border">{p.employee.employeeid}</td>
                    <td className="p-2 border">{p.employee.firstname} {p.employee.surname}</td>
                    <td className="p-2 border">{p.employee.department}</td>
                    <td className="p-2 border">{p.period}</td>
                    <td className="p-2 border">{p.base_salary_usd}</td>
                    <td className="p-2 border">{p.base_salary_zig}</td>
                    <td className="p-2 border">{p.exchange_rate}</td>
                    <td className="p-2 border">{p.net_salary_usd}</td>
                    <td className="p-2 border">{p.net_salary_zig}</td>
                    <td className="p-2 border">{p.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
