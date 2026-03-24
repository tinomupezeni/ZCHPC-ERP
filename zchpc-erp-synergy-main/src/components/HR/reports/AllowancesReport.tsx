// src/components/AllowancesReport.jsx
import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { motion } from "framer-motion";
import jsPDF from "jspdf";
import "jspdf-autotable";
import { toast } from "sonner";

const API_URL = import.meta.env.VITE_API_URL || '';

export default function AllowancesReport() {
  const [allowancesData, setAllowancesData] = useState([]);

  useEffect(() => {
    const fetchAllowancesData = async () => {
      try {
        const res = await fetch(`${API_URL}/api/allowances/`);
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();
        setAllowancesData(data);
      } catch (err) {
        console.error("Error fetching allowances data:", err);
        toast.error("Failed to load allowances report.");
      }
    };
    fetchAllowancesData();
  }, []);

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text("Employee Allowances Report", 14, 16);
    doc.autoTable({
      startY: 20,
      head: [
        [
          "Employee ID",
          "Name",
          "Period",
          "Description",
          "Amount (USD)",
          "Amount (ZiG)",
        ],
      ],
      body: allowancesData.map((item) => [
        item.employee.employeeid,
        `${item.employee.firstname} ${item.employee.surname}`,
        item.period,
        item.description,
        item.amount_usd,
        item.amount_zig,
      ]),
    });
    doc.save("employee_allowances_report.pdf");
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Card className="p-4 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Employee Allowances Report</h2>
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
                  <th className="p-2 border">Period</th>
                  <th className="p-2 border">Description</th>
                  <th className="p-2 border">Amount (USD)</th>
                  <th className="p-2 border">Amount (ZiG)</th>
                </tr>
              </thead>
              <tbody>
                {allowancesData.length > 0 ? (
                  allowancesData.map((item) => (
                    <tr key={`${item.employee.employeeid}-${item.period}-${item.description}`}>
                      <td className="p-2 border">{item.employee.employeeid}</td>
                      <td className="p-2 border">
                        {item.employee.firstname} {item.employee.surname}
                      </td>
                      <td className="p-2 border">{item.period}</td>
                      <td className="p-2 border">{item.description}</td>
                      <td className="p-2 border">{item.amount_usd}</td>
                      <td className="p-2 border">{item.amount_zig}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="p-4 text-center text-gray-500">
                      No allowances data available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}