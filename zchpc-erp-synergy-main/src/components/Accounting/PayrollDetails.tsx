// src/components/Accounting/PayrollDetails.tsx
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import * as XLSX from "xlsx";

interface EmployeePayroll {
  id: number;
  name: string;
  bank: string;
  accountNumber: string;
  netPay: number;
  status: "Pending" | "Paid";
}

interface PayrollDetailsProps {
  payrollBatch: string;
  data: EmployeePayroll[];
}

const PayrollDetails = ({ payrollBatch, data }: PayrollDetailsProps) => {
  const exportToExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(
      data.map((e) => ({
        Name: e.name,
        Bank: e.bank,
        Account: e.accountNumber,
        "Net Pay": e.netPay,
        Status: e.status,
      }))
    );
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, payrollBatch);
    XLSX.writeFile(workbook, `${payrollBatch}_Payroll.xlsx`);
  };

  return (
    <Card className="shadow-md">
      <CardHeader className="flex justify-between items-center">
        <CardTitle>{payrollBatch} - Employee Payroll Details</CardTitle>
        <Button size="sm" variant="default" onClick={exportToExcel}>
          Export to Excel
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Bank</TableHead>
              <TableHead>Account Number</TableHead>
              <TableHead>Net Pay</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((emp) => (
              <TableRow key={emp.id}>
                <TableCell>{emp.name}</TableCell>
                <TableCell>{emp.bank}</TableCell>
                <TableCell>{emp.accountNumber}</TableCell>
                <TableCell>${emp.netPay.toLocaleString()}</TableCell>
                <TableCell>{emp.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default PayrollDetails;
