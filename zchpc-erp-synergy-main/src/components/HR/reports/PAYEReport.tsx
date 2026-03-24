// src/components/PAYEReport.jsx
import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { motion } from "framer-motion";
import jsPDF from "jspdf";
import "jspdf-autotable";
import { toast } from "sonner";

const API_URL = import.meta.env.VITE_API_URL || '';

export default function PAYEReport() {
  const [payeData, setPayeData] = useState([]);

  useEffect(() => {
    // Fetch PAYE data from your backend API
    fetch(`${API_URL}/api/paye/`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => setPayeData(data))
      .catch((err) => {
        console.error("Error fetching PAYE data:", err);
        toast.error("Failed to load PAYE report.");
      });
  }, []);

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text("ZIMRA PAYE Report", 14, 16);
    doc.autoTable({
      startY: 20,
      head: [
        [
          "Employee ID",
          "Name",
          "Gross Income (USD)",
          "Taxable Income (USD)",
          "PAYE Amount (USD)",
          "Gross Income (ZiG)",
          "Taxable Income (ZiG)",
          "PAYE Amount (ZiG)",
        ],
      ],
      body: payeData.map((item) => [
        item.employee.employeeid,
        `${item.employee.firstname} ${item.employee.surname}`,
        item.gross_income_usd,
        item.taxable_income_usd,
        item.paye_amount_usd,
        item.gross_income_zig,
        item.taxable_income_zig,
        item.paye_amount_zig,
      ]),
    });
    doc.save("zimra_paye_report.pdf");
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Card className="p-4 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">ZIMRA PAYE Report</h2>
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
                  <th className="p-2 border">Gross Income (USD)</th>
                  <th className="p-2 border">Taxable Income (USD)</th>
                  <th className="p-2 border">PAYE Amount (USD)</th>
                  <th className="p-2 border">Gross Income (ZiG)</th>
                  <th className="p-2 border">Taxable Income (ZiG)</th>
                  <th className="p-2 border">PAYE Amount (ZiG)</th>
                </tr>
              </thead>
              <tbody>
                {payeData.length > 0 ? (
                  payeData.map((item) => (
                    <tr key={`${item.employee.employeeid}`}>
                      <td className="p-2 border">{item.employee.employeeid}</td>
                      <td className="p-2 border">
                        {item.employee.firstname} {item.employee.surname}
                      </td>
                      <td className="p-2 border">{item.gross_income_usd}</td>
                      <td className="p-2 border">{item.taxable_income_usd}</td>
                      <td className="p-2 border">{item.paye_amount_usd}</td>
                      <td className="p-2 border">{item.gross_income_zig}</td>
                      <td className="p-2 border">{item.taxable_income_zig}</td>
                      <td className="p-2 border">{item.paye_amount_zig}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" className="p-4 text-center text-gray-500">
                      No PAYE data available.
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