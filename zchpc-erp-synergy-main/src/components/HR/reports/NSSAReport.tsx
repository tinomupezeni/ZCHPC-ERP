// src/components/NSSAReport.jsx
import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { motion } from "framer-motion";
import jsPDF from "jspdf";
import "jspdf-autotable";
import { toast } from "sonner";

const API_URL = import.meta.env.VITE_API_URL || '';

export default function NSSAReport() {
  const [nssaData, setNssaData] = useState([]);

  useEffect(() => {
    const fetchNSSAData = async () => {
      try {
        const res = await fetch(`${API_URL}/api/nssa/`);
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();
        setNssaData(data);
      } catch (err) {
        console.error("Error fetching NSSA data:", err);
        toast.error("Failed to load NSSA report.");
      }
    };
    fetchNSSAData();
  }, []);

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text("NSSA Report", 14, 16);
    doc.autoTable({
      startY: 20,
      head: [
        [
          "Employee ID",
          "Name",
          "Period",
          "Contribution (USD)",
          "Contribution (ZiG)",
        ],
      ],
      body: nssaData.map((item) => [
        item.employee.employeeid,
        `${item.employee.firstname} ${item.employee.surname}`,
        item.period,
        item.nssa_contribution_usd,
        item.nssa_contribution_zig,
      ]),
    });
    doc.save("nssa_report.pdf");
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Card className="p-4 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">NSSA Report</h2>
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
                  <th className="p-2 border">Contribution (USD)</th>
                  <th className="p-2 border">Contribution (ZiG)</th>
                </tr>
              </thead>
              <tbody>
                {nssaData.length > 0 ? (
                  nssaData.map((item) => (
                    <tr key={`${item.employee.employeeid}-${item.period}`}>
                      <td className="p-2 border">{item.employee.employeeid}</td>
                      <td className="p-2 border">
                        {item.employee.firstname} {item.employee.surname}
                      </td>
                      <td className="p-2 border">{item.period}</td>
                      <td className="p-2 border">{item.nssa_contribution_usd}</td>
                      <td className="p-2 border">{item.nssa_contribution_zig}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="p-4 text-center text-gray-500">
                      No NSSA data available.
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