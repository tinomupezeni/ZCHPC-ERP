// src/components/LeaveBalanceReport.jsx
import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { motion } from "framer-motion";
import jsPDF from "jspdf";
import "jspdf-autotable";
import { toast } from "sonner";

const API_URL = import.meta.env.VITE_API_URL || '';

export default function LeaveBalanceReport() {
  const [leaveBalances, setLeaveBalances] = useState([]);

  useEffect(() => {
    // Fetch leave balance data from your backend API
    fetch(`${API_URL}/api/leavebalances/`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => setLeaveBalances(data))
      .catch((err) => {
        console.error("Error fetching leave balances:", err);
        toast.error("Failed to load leave balance report.");
      });
  }, []);

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text("Leave Balance Report", 14, 16);
    doc.autoTable({
      startY: 20,
      head: [
        [
          "Employee ID",
          "Name",
          "Department",
          "Leave Type",
          "Days Allocated",
          "Days Taken",
          "Remaining",
          "Status",
        ],
      ],
      body: leaveBalances.map((item) => [
        item.employee.employeeid,
        `${item.employee.firstname} ${item.employee.surname}`,
        item.employee.department,
        item.leave_type,
        item.days_allocated,
        item.days_taken,
        item.remaining_days,
        item.status,
      ]),
    });
    doc.save("leave_balance_report.pdf");
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Card className="p-4 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Leave Balance Report</h2>
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
                  <th className="p-2 border">Leave Type</th>
                  <th className="p-2 border">Days Allocated</th>
                  <th className="p-2 border">Days Taken</th>
                  <th className="p-2 border">Remaining</th>
                  <th className="p-2 border">Status</th>
                </tr>
              </thead>
              <tbody>
                {leaveBalances.length > 0 ? (
                  leaveBalances.map((item) => (
                    <tr key={`${item.employee.employeeid}-${item.leave_type}`}>
                      <td className="p-2 border">{item.employee.employeeid}</td>
                      <td className="p-2 border">
                        {item.employee.firstname} {item.employee.surname}
                      </td>
                      <td className="p-2 border">{item.employee.department}</td>
                      <td className="p-2 border">{item.leave_type}</td>
                      <td className="p-2 border">{item.days_allocated}</td>
                      <td className="p-2 border">{item.days_taken}</td>
                      <td className="p-2 border">{item.remaining_days}</td>
                      <td className="p-2 border">{item.status}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" className="p-4 text-center text-gray-500">
                      No leave balance data available.
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